from __future__ import annotations

import base64
import json
import os
from io import BytesIO

from fastapi import HTTPException
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, ValidationError
from pypdf import PdfReader

from app.observability.logging import logger

SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
}
SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    *SUPPORTED_IMAGE_TYPES,
}
MAX_CV_FILE_SIZE_BYTES = 10 * 1024 * 1024
CV_PARSE_MODEL = os.getenv("CV_PARSE_MODEL", "gpt-4o")

CV_PARSE_SYSTEM_PROMPT = """
You extract work experience entries from CV documents.

Your role is NOT:
- a career coach
- a CV writer
- a generic OCR narrator
- a recruiter

OBJECTIVE:
Return only structured professional experiences found in the uploaded CV.

RULES:
- Do not invent any title, company, or period.
- Use only information explicitly present in the document.
- Keep the order found in the document.
- Return only relevant experience entries.
- Exclude education, certifications, languages, tools, and profile summaries unless they are clearly part of a work experience entry.
- If a field is missing for an experience, return an empty string for that field.
- Normalize obvious whitespace issues, but do not rewrite the meaning.
- PDF text may contain extraction artifacts such as words split by unexpected spaces.
- Reconstruct obvious split words when reading the source text, but do not invent missing experience entries.

STRICT OUTPUT CONTRACT:
Return only a JSON object with this exact structure:
{
  "experiences": [
    {
      "title": "",
      "company": "",
      "period": ""
    }
  ]
}

All fields must be strings.
No markdown.
No explanations.
No additional keys.
"""


class CVExperience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    company: str
    period: str


class CVParseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiences: list[CVExperience]


def ensure_supported_cv_upload(content_type: str | None) -> str:
    normalized = (content_type or "").strip().lower()
    if normalized not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Supported types: application/pdf, image/jpeg, image/png",
        )
    return normalized


def ensure_cv_file_size(file_bytes: bytes) -> None:
    if len(file_bytes) > MAX_CV_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"CV file is too large. Maximum size is {MAX_CV_FILE_SIZE_BYTES} bytes",
        )


def parse_cv_file(*, filename: str, content_type: str, file_bytes: bytes) -> CVParseResponse:
    ensure_cv_file_size(file_bytes)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("CV parse rejected reason=missing_openai_api_key")
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY environment variable is missing")

    client = OpenAI(api_key=api_key)

    if content_type == "application/pdf":
        extracted_text = _extract_text_from_pdf(file_bytes)
        if not extracted_text.strip():
            logger.warning("CV parse rejected reason=empty_pdf_text filename=%s", filename)
            raise HTTPException(
                status_code=422,
                detail="No extractable text was found in the PDF. Image-based PDFs are not currently supported.",
            )
        return _parse_cv_text(client=client, filename=filename, extracted_text=extracted_text)

    return _parse_cv_image(
        client=client,
        filename=filename,
        content_type=content_type,
        file_bytes=file_bytes,
    )


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()


def _parse_cv_text(*, client: OpenAI, filename: str, extracted_text: str) -> CVParseResponse:
    payload = {
        "filename": filename,
        "document_type": "cv_pdf_text",
        "content": extracted_text,
    }
    return _call_cv_parse_model(
        client=client,
        messages=[
            {"role": "system", "content": CV_PARSE_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
    )


def _parse_cv_image(*, client: OpenAI, filename: str, content_type: str, file_bytes: bytes) -> CVParseResponse:
    image_data = base64.b64encode(file_bytes).decode("utf-8")
    user_content = [
        {
            "type": "text",
            "text": (
                "Extract the professional experience entries from this CV image. "
                f"Filename: {filename}. "
                "Return only the required JSON object."
            ),
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{content_type};base64,{image_data}",
            },
        },
    ]
    return _call_cv_parse_model(
        client=client,
        messages=[
            {"role": "system", "content": CV_PARSE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )


def _call_cv_parse_model(client: OpenAI, messages: list[dict[str, object]]) -> CVParseResponse:
    try:
        completion = client.chat.completions.create(
            model=CV_PARSE_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        logger.exception("CV parse OpenAI call failed model=%s", CV_PARSE_MODEL)
        raise HTTPException(status_code=500, detail=f"OpenAI API call failed: {exc}") from exc

    content = completion.choices[0].message.content if completion.choices else None
    if not content:
        logger.warning("CV parse failed reason=empty_model_response model=%s", CV_PARSE_MODEL)
        raise HTTPException(status_code=500, detail="OpenAI response did not contain content")

    try:
        parsed = json.loads(content)
    except Exception as exc:
        logger.warning("CV parse failed reason=invalid_json model=%s", CV_PARSE_MODEL)
        raise HTTPException(status_code=500, detail=f"Failed to parse model response as JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        logger.warning("CV parse failed reason=not_json_object model=%s", CV_PARSE_MODEL)
        raise HTTPException(status_code=500, detail="Parsed model response is not a JSON object")

    try:
        return CVParseResponse.model_validate(parsed)
    except ValidationError as exc:
        logger.warning("CV parse failed reason=invalid_response_schema model=%s", CV_PARSE_MODEL)
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
