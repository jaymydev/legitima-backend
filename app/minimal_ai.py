import json
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, ValidationError
from dotenv import load_dotenv

load_dotenv()


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
- Argumentative
- Non-emotional
- No inspiration
- No encouragement
- No coaching tone

If information is insufficient:
- Do not invent data.
- Use only available information.
- Remain factual.

If output deviates from structure, the response is invalid.
"""


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input: Dict[str, Any]


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


app = FastAPI()


@app.post("/analyze", response_model=AnalyzeResponseV1)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponseV1:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY environment variable is missing")

    client = OpenAI(api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_V1},
                {"role": "user", "content": json.dumps(payload.input)},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI API call failed: {exc}") from exc

    content = completion.choices[0].message.content if completion.choices else None
    if not content:
        raise HTTPException(status_code=500, detail="OpenAI response did not contain content")

    try:
        parsed = json.loads(content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse model response as JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=500, detail="Parsed model response is not a JSON object")

    try:
        return AnalyzeResponseV1.model_validate(parsed)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
