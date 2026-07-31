from __future__ import annotations

from fastapi import APIRouter

from app.api.rate_limit import limiter

router = APIRouter()


# Render polls this continuously to decide whether the service is alive.
# Counting those calls would exhaust the default bucket on its own and take
# the service down with it.
@limiter.exempt
@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
