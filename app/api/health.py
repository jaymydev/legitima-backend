from __future__ import annotations

from fastapi import APIRouter

from app.api.rate_limit import limiter
from app.services.cv_parse import ocr_availability

router = APIRouter()


# Render polls this continuously to decide whether the service is alive.
# Counting those calls would exhaust the default bucket on its own and take
# the service down with it.
@limiter.exempt
@router.get("/health")
def health() -> dict[str, object]:
    # `ocr` is here because its absence once shipped to production unnoticed:
    # the native Python runtime has the pytesseract package but no tesseract
    # binary, so CV photos failed while every other route looked healthy.
    return {"status": "ok", "ocr": ocr_availability()}
