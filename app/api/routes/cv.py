import time
from typing import Annotated, Optional

from fastapi import APIRouter, File, Header, HTTPException, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.api.rate_limit import CV_PARSE_LIMIT, limiter
from app.services.cv_parse import (
    CVParseResponse,
    ensure_supported_cv_upload,
    maybe_raise_cv_parse_test_error,
    parse_cv_file,
)
from app.observability.logging import logger

router = APIRouter()


@router.post("/cv/parse", response_model=CVParseResponse, tags=["CV"])
@limiter.limit(CV_PARSE_LIMIT)
async def parse_cv(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    test_error: Annotated[Optional[str], Header(alias="X-CV-Parse-Test-Error")] = None,
) -> CVParseResponse:
    maybe_raise_cv_parse_test_error(test_error)
    started_at = time.perf_counter()
    content_type = ensure_supported_cv_upload(file.content_type)
    file_bytes = await file.read()
    # PDF extraction and OCR are blocking operations; keep them off the event loop.
    try:
        return await run_in_threadpool(
            parse_cv_file,
            filename=file.filename or "uploaded-cv",
            content_type=content_type,
            file_bytes=file_bytes,
            started_at=started_at,
        )
    except HTTPException as exc:
        logger.warning(
            "CV parse failed content_type=%s file_size_bytes=%d status_code=%d total_duration_ms=%d",
            content_type,
            len(file_bytes),
            exc.status_code,
            round((time.perf_counter() - started_at) * 1000),
        )
        raise
    except Exception:
        logger.exception(
            "CV parse failed unexpectedly content_type=%s file_size_bytes=%d total_duration_ms=%d",
            content_type,
            len(file_bytes),
            round((time.perf_counter() - started_at) * 1000),
        )
        raise
