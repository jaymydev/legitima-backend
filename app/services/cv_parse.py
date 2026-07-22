from __future__ import annotations

import os
import re
import unicodedata
from io import BytesIO
from time import perf_counter
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
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
CV_PARSE_OCR_TIMEOUT_SECONDS = 20
CV_PARSE_OCR_MAX_IMAGE_DIMENSION = 2400
CV_PARSE_OCR_SIDEBAR_RATIO = 0.34
ENABLE_CV_PARSE_TEST_ERRORS_ENV = "ENABLE_CV_PARSE_TEST_ERRORS"
CV_PARSE_TEST_ERROR_500 = "500"

_MONTH_RE = (
    r"janvier|janv?\.?|f[eé]vrier|f[eé]vr?\.?|mars|avril|avr\.?|mai|juin|"
    r"juillet|juil?\.?|ao[uû]t|septembre|sept?\.?|octobre|oct\.?|novembre|nov\.?|d[eé]cembre|d[eé]c\.?"
)
_PERIOD_RE = re.compile(
    r"(?ix)"
    r"(?:"
    r"(?:\d{1,2}[\s./-])?\d{1,2}[\s./-]\d{2,4}(?!\s*%)"
    rf"|(?:depuis\s+)?(?:{_MONTH_RE})\s+\d{{4}}"
    r"|\d{4}\s*(?:[–—-]|à|au)\s*(?:\d{4}|aujourd'hui|aujourd’hui|présent|present|now)"
    r"|\d{4}\s*(?:[–—-]|à|au)\s*\d{4}"
    r"|\d{4}"
    r")"
)
_SEPARATOR_RE = re.compile(r"\s+(?:-|–|—|\|)\s+")
_KNOWN_COMPANY_CONTEXT_RE = re.compile(
    r"(?P<company>\baccenture\b(?:\s*\([^)]*\))?)",
    flags=re.IGNORECASE,
)
_LEADING_MONTH_FRAGMENT_RE = re.compile(r"^(?P<month>[A-Za-zÀ-ÿ.]+)\s+(?:-|–|—|\|)\s+(?P<rest>.+)$")
_LEADING_OCR_NOISE_RE = re.compile(r"^[\s+©®*#•●·]+")
_CANONICAL_MONTHS = (
    "janvier",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "decembre",
)


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


def maybe_raise_cv_parse_test_error(test_error: str | None) -> None:
    if (test_error or "").strip() != CV_PARSE_TEST_ERROR_500:
        return
    if os.getenv(ENABLE_CV_PARSE_TEST_ERRORS_ENV, "").strip().lower() != "true":
        return
    raise HTTPException(status_code=500, detail="Forced /cv/parse test error")


def parse_cv_file(
    *,
    filename: str,
    content_type: str,
    file_bytes: bytes,
    started_at: float | None = None,
) -> CVParseResponse:
    """Extract work experience without sending the uploaded CV to an LLM."""
    del filename
    started_at = started_at or perf_counter()
    ensure_cv_file_size(file_bytes)
    extraction_started_at = perf_counter()

    if content_type in SUPPORTED_IMAGE_TYPES:
        try:
            extracted_text = _extract_text_from_image(file_bytes)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=422, detail="The image could not be read") from exc

        if not extracted_text.strip():
            raise HTTPException(
                status_code=422,
                detail="No extractable text was found in the image. Upload a readable CV image.",
            )
        response = _response_from_extracted_text(extracted_text)
        _log_parse_timing(
            content_type=content_type,
            file_size_bytes=len(file_bytes),
            extraction_duration_ms=_elapsed_ms(extraction_started_at),
            total_duration_ms=_elapsed_ms(started_at),
            experience_count=len(response.experiences),
        )
        return response

    if content_type != "application/pdf":
        raise HTTPException(
            status_code=422,
            detail="Image CV parsing is not currently supported. Upload a text-based PDF.",
        )

    try:
        extracted_text = _extract_text_from_pdf(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="The PDF could not be read") from exc

    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No extractable text was found in the PDF. Upload a text-based PDF.",
        )
    response = _response_from_extracted_text(extracted_text)
    _log_parse_timing(
        content_type=content_type,
        file_size_bytes=len(file_bytes),
        extraction_duration_ms=_elapsed_ms(extraction_started_at),
        total_duration_ms=_elapsed_ms(started_at),
        experience_count=len(response.experiences),
    )
    return response


def _elapsed_ms(started_at: float) -> int:
    return round((perf_counter() - started_at) * 1000)


def _log_parse_timing(
    *,
    content_type: str,
    file_size_bytes: int,
    extraction_duration_ms: int,
    total_duration_ms: int,
    experience_count: int,
) -> None:
    logger.info(
        "CV parse completed content_type=%s file_size_bytes=%d extraction_duration_ms=%d total_duration_ms=%d experience_count=%d",
        content_type,
        file_size_bytes,
        extraction_duration_ms,
        total_duration_ms,
        experience_count,
    )


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _extract_text_from_image(file_bytes: bytes) -> str:
    try:
        from PIL import Image, ImageOps, ImageStat
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("OCR dependencies are not installed") from exc

    ocr_language = os.getenv("CV_PARSE_OCR_LANG", "fra+eng")
    try:
        image = ImageOps.exif_transpose(Image.open(BytesIO(file_bytes)))
        original_width, original_height = image.size
        image.thumbnail(
            (CV_PARSE_OCR_MAX_IMAGE_DIMENSION, CV_PARSE_OCR_MAX_IMAGE_DIMENSION),
            Image.Resampling.LANCZOS,
        )
        logger.info(
            "CV OCR image prepared original_width=%d original_height=%d processed_width=%d processed_height=%d resized=%s",
            original_width,
            original_height,
            image.width,
            image.height,
            image.size != (original_width, original_height),
        )
        image = ImageOps.autocontrast(image.convert("L"))
        attempts = _build_ocr_attempts(image, image_stat_module=ImageStat)
        return _run_ocr_attempts(
            pytesseract_module=pytesseract,
            attempts=attempts,
            language=ocr_language,
            timeout_seconds=CV_PARSE_OCR_TIMEOUT_SECONDS,
        )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("OCR engine is not available or failed to process the image") from exc


def _build_ocr_attempts(image: Any, *, image_stat_module: Any) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    if _has_dark_left_sidebar(image, image_stat_module=image_stat_module):
        split_x = max(1, int(image.width * CV_PARSE_OCR_SIDEBAR_RATIO))
        attempts.append(
            {
                "label": "main_column",
                "image": image.crop((split_x, 0, image.width, image.height)),
                "config": "--psm 4",
            }
        )
    attempts.append(
        {
            "label": "full_page",
            "image": image,
            "config": "--psm 3",
        }
    )
    return attempts


def _has_dark_left_sidebar(image: Any, *, image_stat_module: Any) -> bool:
    if image.width < 800 or image.height < 1000:
        return False
    split_x = max(1, int(image.width * CV_PARSE_OCR_SIDEBAR_RATIO))
    left = image.crop((0, 0, split_x, image.height))
    right = image.crop((split_x, 0, image.width, image.height))
    left_mean = image_stat_module.Stat(left).mean[0]
    right_mean = image_stat_module.Stat(right).mean[0]
    return (right_mean - left_mean) >= 45


def _run_ocr_attempts(
    *,
    pytesseract_module: Any,
    attempts: list[dict[str, Any]],
    language: str,
    timeout_seconds: int,
) -> str:
    started_at = perf_counter()
    last_error: RuntimeError | None = None

    for attempt in attempts:
        remaining_seconds = max(1, timeout_seconds - int(perf_counter() - started_at))
        attempt_started_at = perf_counter()
        try:
            text = pytesseract_module.image_to_string(
                attempt["image"],
                lang=language,
                config=attempt["config"],
                timeout=remaining_seconds,
            ).strip()
            logger.info(
                "CV OCR attempt completed label=%s width=%d height=%d config=%s duration_ms=%d remaining_budget_s=%d has_text=%s",
                attempt["label"],
                attempt["image"].width,
                attempt["image"].height,
                attempt["config"],
                _elapsed_ms(attempt_started_at),
                remaining_seconds,
                bool(text),
            )
            if text:
                return text
        except RuntimeError as exc:
            last_error = exc
            logger.warning(
                "CV OCR attempt failed label=%s width=%d height=%d config=%s duration_ms=%d error=%s",
                attempt["label"],
                attempt["image"].width,
                attempt["image"].height,
                attempt["config"],
                _elapsed_ms(attempt_started_at),
                str(exc),
            )
            if "timeout" not in str(exc).lower():
                raise

    if last_error is not None:
        raise last_error
    return ""


def _response_from_extracted_text(extracted_text: str) -> CVParseResponse:
    result = parse_cv_text(extracted_text)
    if not result.experiences:
        raise HTTPException(
            status_code=422,
            detail="No exploitable professional experiences were found in this document. Verify that it is a readable CV.",
        )
    return result


def parse_cv_text(extracted_text: str) -> CVParseResponse:
    lines = _normalise_lines(extracted_text)
    experience_lines = _experience_section(lines)
    experiences: list[CVExperience] = []
    current_company = ""

    for index, line in enumerate(experience_lines):
        if _looks_like_company(line) and len(line) <= 80:
            current_company = _clean(line)
        if line.lstrip().startswith("-") and not _has_period(line):
            continue
        if not _has_period(line):
            continue
        if index > 0 and line.lstrip().startswith(("-", "(")):
            candidate = _experience_from_line(f"{experience_lines[index - 1]} {line}") or candidate
        else:
            candidate = _experience_from_line(line)
        if index > 0 and (candidate is None or (not candidate.company and ":" not in line)):
            previous = _previous_experience_line(experience_lines, index)
            if previous is None:
                previous = experience_lines[index - 1]
            if line.lstrip().startswith("("):
                previous = f"{previous} {line}"
            adjacent = _experience_from_adjacent_lines(previous, line)
            if adjacent is not None:
                candidate = adjacent
        if candidate is not None and not candidate.company and current_company:
            candidate = CVExperience(title=candidate.title, company=current_company, period=candidate.period)
        if candidate is not None:
            experiences.append(candidate)

    return CVParseResponse(experiences=_deduplicate(experiences))


def _normalise_lines(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00a0", " ").replace("–", "-").replace("—", "-")
    return [re.sub(r"\s+", " ", line).strip(" •●\t") for line in text.splitlines() if line.strip()]


def _experience_section(lines: list[str]) -> list[str]:
    result: list[str] = []
    in_experience_section = False
    for line in lines:
        if _is_experience_heading(line):
            in_experience_section = True
            continue
        if _is_section_end_heading(line):
            in_experience_section = False
        elif in_experience_section:
            result.append(line)
    return result


def _heading_key(line: str) -> str:
    decomposed = unicodedata.normalize("NFD", line)
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z ]", " ", without_accents)).strip().casefold()


def _is_experience_heading(line: str) -> bool:
    key = _heading_key(line).replace(" ", "")
    return key in {"experiences", "experience", "experiencesprofessionnelles", "parcoursprofessionnel"}


def _is_section_end_heading(line: str) -> bool:
    key = _heading_key(line).replace(" ", "")
    return key.startswith(
        (
            "formation",
            "education",
            "certification",
            "competence",
            "skill",
            "langue",
            "centresinteret",
            "interests",
            "aboutme",
            "motscles",
            "personnalite",
        )
    )


def _has_period(line: str) -> bool:
    return bool(_PERIOD_RE.search(line))


def _experience_from_line(line: str) -> CVExperience | None:
    match = _PERIOD_RE.search(line)
    if not match:
        return None
    period = _period_from_match(line, match)
    before = _clean(line[: match.start()])
    if not before:
        return None
    before, period = _reattach_leading_month_fragment(before, period)
    if not before:
        return None

    known_company = _experience_with_known_company_context(before, period)
    if known_company is not None:
        return known_company

    trailing_title = re.search(
        r"(?i)(?P<title>(?:d[eé]veloppeur|d[eé]veloppeuse|testeur|testeuse|consultant(?:e)?|ing[eé]nieur(?:e)?|assistant(?:e)?|technicien(?:ne)?)[^:]{0,80})$",
        before,
    )
    if trailing_title:
        return CVExperience(title=_clean(trailing_title.group("title")), company="", period=period)

    parts = _SEPARATOR_RE.split(before, maxsplit=1)
    if len(parts) == 2:
        left, right = map(_clean, parts)
        if _looks_like_role_title(left):
            return CVExperience(title=left, company=right, period=period)
        if _looks_like_company(left) and not _looks_like_company(right):
            return CVExperience(title=right, company=left, period=period)
        return CVExperience(title=left, company=right, period=period)

    embedded_company = re.search(
        r"(?P<title>.+?)\s+(?P<company>[A-Z][A-Za-zÀ-ÿ&.'-]*)\s*\(",
        before,
    )
    if embedded_company:
        return CVExperience(
            title=_clean(embedded_company.group("title")),
            company=_clean(embedded_company.group("company")),
            period=period,
        )

    # Common CV layout: "Title Company (mission...) | date".
    organisation = re.search(r"(?P<title>.+?)\s+(?P<company>[A-Z][A-Za-zÀ-ÿ&.' -]{2,})(?=\s*(?:\(|$))", before)
    if organisation:
        return CVExperience(
            title=_clean(organisation.group("title")),
            company=_clean(organisation.group("company")),
            period=period,
        )

    return CVExperience(title=before, company="", period=period)


def _experience_with_known_company_context(before: str, period: str) -> CVExperience | None:
    matches = list(_KNOWN_COMPANY_CONTEXT_RE.finditer(before))
    if not matches:
        return None
    match = matches[-1]
    title = _clean(before[: match.start()])
    company = _clean(match.group("company"))
    if not title or not company:
        return None
    return CVExperience(title=title, company=company, period=period)


def _experience_from_adjacent_lines(previous: str, current: str) -> CVExperience | None:
    match = _PERIOD_RE.search(current)
    if not match:
        return None
    current_without_period = _clean(current[: match.start()])
    period = _period_from_match(current, match)
    current_without_period, period = _reattach_leading_month_fragment(current_without_period, period)
    parts = _SEPARATOR_RE.split(current_without_period, maxsplit=1)
    if len(parts) == 2:
        title, company = map(_clean, parts)
    elif not current_without_period:
        if "(" in previous:
            combined = _experience_from_line(f"{previous} - {period}")
            if combined is not None and combined.company:
                return combined
        parts = _SEPARATOR_RE.split(previous, maxsplit=1)
        if len(parts) != 2:
            return None
        left, right = map(_clean, parts)
        if _looks_like_role_title(right) and not _looks_like_role_title(left):
            title, company = right, left
        elif _looks_like_role_title(left):
            title, company = left, right
        elif _looks_like_company(left) and not _looks_like_company(right):
            company, title = left, right
        else:
            title, company = left, right
    else:
        title, company = current_without_period, _clean(previous)
    if not title:
        return None
    return CVExperience(title=title, company=company, period=period)


def _previous_experience_line(lines: list[str], current_index: int) -> str | None:
    for line in reversed(lines[:current_index]):
        stripped = line.strip()
        if not stripped or stripped.startswith(("-", "•", "●")):
            continue
        if _has_period(stripped):
            continue
        if stripped.endswith("."):
            continue
        if _looks_like_company(stripped) or _SEPARATOR_RE.search(stripped) or _looks_like_role_title(stripped):
            return stripped
    return None


def _period_from_match(line: str, match: re.Match[str]) -> str:
    period = match.group(0)
    suffix = line[match.end() :]
    continuation = re.match(
        rf"\s*(?:-|à|au)\s*(?:(?:{_MONTH_RE})\s+\d{{4}}|(?:\d{{1,2}}[\s./-])?\d{{1,2}}[\s./-]\d{{2,4}}|\d{{4}}|aujourd'hui|aujourd’hui|présent|present|now)",
        suffix,
        flags=re.IGNORECASE,
    )
    if continuation:
        period += continuation.group(0)
    return _clean(period)


def _looks_like_company(value: str) -> bool:
    words = [word for word in value.split() if word]
    return bool(words) and (value.upper() == value or any(token in value.lower() for token in ("sarl", "sas", "airbus", "capgemini")))


def _looks_like_role_title(value: str) -> bool:
    return bool(
        re.search(
            r"(?i)\b("
            r"assistant(?:e)?|administrati(?:f|ve)|coordina(?:teur|trice)|consultant(?:e)?|"
            r"d[eé]veloppeur|d[eé]veloppeuse|employ[eé]e?|technicien(?:ne)?|ing[eé]nieur(?:e)?|"
            r"responsable|chef(?:fe)?|manager|lead|testeur|testeuse"
            r")\b",
            value,
        )
    )


def _clean(value: str) -> str:
    compact = re.sub(r"\s+", " ", value).strip(" -|,;:")
    return _LEADING_OCR_NOISE_RE.sub("", compact)


def _reattach_leading_month_fragment(before: str, period: str) -> tuple[str, str]:
    match = _LEADING_MONTH_FRAGMENT_RE.match(before)
    if not match:
        return before, period
    normalized_month = _normalize_month_fragment(match.group("month"))
    if normalized_month is None:
        return before, period
    if not re.match(r"^\d{4}\b", period):
        return before, period
    return _clean(match.group("rest")), f"{normalized_month} {period}"


def _normalize_month_fragment(value: str) -> str | None:
    normalized = _heading_key(value).replace(" ", "")
    if not normalized:
        return None
    for month in _CANONICAL_MONTHS:
        if normalized == month:
            return month.capitalize()
        if len(month) >= 4 and normalized == month[1:]:
            return month.capitalize()
    return None


def _deduplicate(experiences: list[CVExperience]) -> list[CVExperience]:
    seen: set[tuple[str, str, str]] = set()
    result: list[CVExperience] = []
    for experience in experiences:
        key = (experience.title.casefold(), experience.company.casefold(), experience.period.casefold())
        if key not in seen:
            seen.add(key)
            result.append(experience)
    return result
