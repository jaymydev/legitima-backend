import json
import os
import re
import unicodedata
from typing import Iterable

from fastapi import APIRouter, Request, Response
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from app.api.errors import (
    ANALYSIS_GENERATION_FAILED,
    ANALYSIS_INVALID_MODEL_RESPONSE,
    ANALYSIS_QUALITY_INSUFFICIENT,
    SERVICE_UNAVAILABLE,
    user_facing_error,
)
from app.api.rate_limit import AI_GENERATION_LIMIT, limiter
from app.observability.logging import logger
from app.services.french_quality import (
    ENGLISH_MARKERS,
    REQUIRED_FRENCH_ACCENTS,
    contains_english_markers as _contains_english_markers,
    contains_missing_required_accents as _contains_missing_required_accents,
)

router = APIRouter()


SYSTEM_PROMPT_V1 = """
You are an AI engine acting as a strategic reading system for professional career analysis.

Your role is NOT:
- a motivational coach
- a psychologist
- a recruiter
- a CV corrector
- a conversational chatbot

Your role is to transform a raw professional background into a structured, defensible, rational strategic synthesis.

OBJECTIVE:
Transform a fragmented career path into a coherent, defensible narrative aligned with a targeted role.

You must:
1. Identify functional logic behind the career path.
2. Extract objectively developed competencies.
3. Neutralize fragile periods without defensive justification.
4. Build a coherent core thread aligned with the target role.
5. Anticipate realistic objections.
6. Provide structured, rational responses.
7. Anchor legitimacy in objective competence and demonstrated coherence.

STRICT INPUT CONTRACT:
You receive a JSON strictly conforming to INPUT V1.
All fields are strings.
You must not invent data.
You must not reformulate the input JSON.
You must analyze it.
You are strictly forbidden from adding any field not explicitly listed in the OUTPUT structure.
Any deviation invalidates the response.

OUTPUT LANGUAGE RULE:
- The requested output language is determined by `input.meta.language`.
- If `input.meta.language` is `fr`, every output field must be written strictly in French.
- Do not include English words, English headings, or mixed French/English phrasing.
- If a concept can be expressed in French, express it in French.
- Use correct French spelling and accents.
- Do not omit accents in standard French words when they are required.
- Example: write `expérimenté`, not `experimente`.

FIELD DISTINCTNESS RULE:
- Each output field must provide distinct value and purpose.
- Do not copy the same sentence into multiple fields.
- Do not repeat the same paragraph under different labels.
- Each field must add new information adapted to its label.

STRICT SEPARATION RULE:

The OUTPUT structure is independent from INPUT.
You must not reuse or mirror any INPUT field names.
You must not echo INPUT section names.
You must not add any field derived from INPUT keys.

Only the fields explicitly listed in the OUTPUT structure are allowed.
No others.

STRICT OUTPUT CONTRACT:
You must return ONLY a JSON object.
No markdown.
No explanations.
No commentary.
No text outside JSON.
No additional fields.
No missing fields.

The JSON must follow EXACTLY this structure:

{
  "analysis": {
    "strategic_reading": "",
    "dominant_competencies": "",
    "career_logic": ""
  },
  "sensitive_reframing": {
    "identified_fragilities": "",
    "strategic_reinterpretation": "",
    "rational_reframing": ""
  },
  "narrative": {
    "core_thread": "",
    "positioning_statement": ""
  },
  "interview_preparation": {
    "probable_objections": "",
    "structured_answers": ""
  },
  "legitimacy_anchor": {
    "objective_strength": "",
    "final_alignment_statement": ""
  }
}

All fields must be strings.

TONE:
- Structured
- Rational
- Professional
- Clear
- Grounded
- Reassuring without exaggeration
- Non-judgmental
- Avoid unnecessary jargon
- No inspiration
- No empty encouragement
- No coaching tone

If information is insufficient:
- Do not invent data.
- Use only available information.
- Remain factual.

If output deviates from structure, the response is invalid.
"""

FRENCH_RETRY_PROMPT = """
The previous answer did not satisfy the output quality rules.

Return the same JSON structure again, but every value must be written strictly in French.
Do not include English words.
Use correct French spelling with accents.
Do not repeat the same text across multiple fields.
Do not change the schema.
Do not add fields.
Do not remove fields.
"""

ANALYZE_MODEL = "gpt-4o-mini"


class AnalyzeMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    language: str
    target_market: str
    interview_type: str

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized != "fr":
            raise ValueError("Only French output is currently supported for /analyze")
        return normalized


class NarrativePositioningInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    short_summary: str
    current_positioning: str
    evolution_logic: str


class AnalyzeInputV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meta: AnalyzeMeta
    narrative_positioning: NarrativePositioningInput


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input: AnalyzeInputV1


class AnalysisSectionV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategic_reading: str
    dominant_competencies: str
    career_logic: str


class SensitiveReframingSectionV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identified_fragilities: str
    strategic_reinterpretation: str
    rational_reframing: str


class NarrativeSectionV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    core_thread: str
    positioning_statement: str


class InterviewPreparationSectionV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    probable_objections: str
    structured_answers: str


class LegitimacyAnchorSectionV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    objective_strength: str
    final_alignment_statement: str


class AnalyzeResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis: AnalysisSectionV1
    sensitive_reframing: SensitiveReframingSectionV1
    narrative: NarrativeSectionV1
    interview_preparation: InterviewPreparationSectionV1
    legitimacy_anchor: LegitimacyAnchorSectionV1


def _build_messages(payload: AnalyzeInputV1, retry_for_french: bool = False) -> list[dict[str, str]]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_V1},
        {"role": "user", "content": json.dumps(payload.model_dump())},
    ]
    if retry_for_french:
        messages.insert(1, {"role": "system", "content": FRENCH_RETRY_PROMPT})
    return messages


def _parse_analysis_response(content: str) -> AnalyzeResponseV1:
    try:
        parsed = json.loads(content)
    except Exception as exc:
        # The reason stays in the log. A decode error quotes the surrounding
        # text, and that text is the model's reading of someone's career.
        logger.warning("Analyze parse failure reason=invalid_json")
        raise user_facing_error(ANALYSIS_GENERATION_FAILED) from exc

    if not isinstance(parsed, dict):
        logger.warning("Analyze parse failure reason=not_json_object")
        raise user_facing_error(ANALYSIS_GENERATION_FAILED)

    try:
        return AnalyzeResponseV1.model_validate(parsed)
    except ValidationError as exc:
        # `exc.errors()` used to be the response body. Pydantic phrases those in
        # English, about fields the caller never sent — they describe the
        # model's answer, not the request.
        logger.warning(
            "Analyze validation failure reason=invalid_response_schema error_count=%d",
            len(exc.errors()),
        )
        raise user_facing_error(ANALYSIS_INVALID_MODEL_RESPONSE) from exc


def _iter_response_strings(response: AnalyzeResponseV1) -> Iterable[str]:
    data = response.model_dump()
    for section in data.values():
        for value in section.values():
            yield value


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", value) if unicodedata.category(char) != "Mn"
    )


def _normalize_for_duplicate_check(text: str) -> str:
    lowered = _strip_accents(text).lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _iter_distinctness_chunks(text: str) -> Iterable[str]:
    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    if len(paragraphs) > 1:
        yield from paragraphs
        return
    yield text


def _contains_duplicate_content(response: AnalyzeResponseV1) -> bool:
    normalized_values = [
        _normalize_for_duplicate_check(chunk)
        for value in _iter_response_strings(response)
        for chunk in _iter_distinctness_chunks(value)
    ]
    seen: set[str] = set()
    for value in normalized_values:
        if len(value) < 20:
            continue
        if value in seen:
            return True
        seen.add(value)
    return False


def _satisfies_french_quality_rules(response: AnalyzeResponseV1) -> bool:
    if any(_contains_english_markers(value) for value in _iter_response_strings(response)):
        return False
    if any(_contains_missing_required_accents(value) for value in _iter_response_strings(response)):
        return False
    if _contains_duplicate_content(response):
        return False
    return True


def _generate_analysis(
    client: OpenAI,
    payload: AnalyzeInputV1,
    retry_for_french: bool = False,
) -> AnalyzeResponseV1:
    attempt = "retry_french" if retry_for_french else "initial"
    try:
        completion = client.chat.completions.create(
            model=ANALYZE_MODEL,
            # The App Store privacy label rests on this: never retained upstream.
            store=False,
            messages=_build_messages(payload, retry_for_french=retry_for_french),
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        logger.exception(
            "Analyze OpenAI call failed attempt=%s language=%s target_market=%s interview_type=%s",
            attempt,
            payload.meta.language,
            payload.meta.target_market,
            payload.meta.interview_type,
        )
        # Never the upstream text: OpenAI answers a bad credential with
        # "Incorrect API key provided: sk-...", and this endpoint takes no
        # authentication, so interpolating it published the key to anyone who
        # asked. `logger.exception` above keeps the detail where it belongs.
        raise user_facing_error(ANALYSIS_GENERATION_FAILED) from exc

    content = completion.choices[0].message.content if completion.choices else None
    if not content:
        logger.warning(
            "Analyze empty model response attempt=%s language=%s target_market=%s interview_type=%s",
            attempt,
            payload.meta.language,
            payload.meta.target_market,
            payload.meta.interview_type,
        )
        raise user_facing_error(ANALYSIS_GENERATION_FAILED)

    return _parse_analysis_response(content)


@router.post("/analyze", response_model=AnalyzeResponseV1, tags=["Analyze"])
@limiter.limit(AI_GENERATION_LIMIT)
def analyze(request: Request, response: Response, payload: AnalyzeRequest) -> AnalyzeResponseV1:
    # `request` is unused by the handler; slowapi reads it to identify the
    # caller, and refuses to decorate a route that does not declare it.
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("Analyze rejected reason=missing_openai_api_key")
        raise user_facing_error(SERVICE_UNAVAILABLE)

    logger.info(
        "Analyze request started language=%s target_market=%s interview_type=%s model=%s",
        payload.input.meta.language,
        payload.input.meta.target_market,
        payload.input.meta.interview_type,
        ANALYZE_MODEL,
    )
    client = OpenAI(api_key=api_key)

    response = _generate_analysis(client, payload.input)
    if _satisfies_french_quality_rules(response):
        logger.info("Analyze request succeeded retried_for_french=false")
        return response

    logger.warning("Analyze response failed quality validation attempt=initial")
    retry_response = _generate_analysis(client, payload.input, retry_for_french=True)
    if _satisfies_french_quality_rules(retry_response):
        logger.info("Analyze request succeeded retried_for_french=true")
        return retry_response

    logger.error("Analyze response failed quality validation attempt=retry_french")
    raise user_facing_error(ANALYSIS_QUALITY_INSUFFICIENT)
