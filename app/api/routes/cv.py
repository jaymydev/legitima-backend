from typing import Annotated, Optional

from fastapi import APIRouter, File, Header, UploadFile

from app.services.cv_parse import (
    CVParseResponse,
    ensure_supported_cv_upload,
    maybe_raise_cv_parse_test_error,
    parse_cv_file,
)

router = APIRouter()


@router.post("/cv/parse", response_model=CVParseResponse, tags=["CV"])
async def parse_cv(
    file: UploadFile = File(...),
    test_error: Annotated[Optional[str], Header(alias="X-CV-Parse-Test-Error")] = None,
) -> CVParseResponse:
    maybe_raise_cv_parse_test_error(test_error)
    content_type = ensure_supported_cv_upload(file.content_type)
    file_bytes = await file.read()
    return parse_cv_file(
        filename=file.filename or "uploaded-cv",
        content_type=content_type,
        file_bytes=file_bytes,
    )
