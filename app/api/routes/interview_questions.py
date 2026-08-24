# Deliberately no `from __future__ import annotations` here. Under postponed
# evaluation FastAPI cannot resolve the body model through slowapi's decorator
# wrapper, and silently downgrades `payload` to a query parameter — every POST
# then answers 422. This cost a production outage once already.

import os

from fastapi import APIRouter, Request, Response
from openai import OpenAI
from pydantic import BaseModel

from app.api.errors import (
    PREPARATION_GENERATION_FAILED,
    PREPARATION_INVALID_REQUEST,
    SERVICE_UNAVAILABLE,
    UNKNOWN_USE_CASE,
    user_facing_error,
)
from app.api.rate_limit import AI_GENERATION_LIMIT, limiter
from app.observability.logging import logger
from app.services.interview_preparation import InterviewUseCase
from app.services.interview_questions import (
    PreparedInterview,
    PreparedInterviewRequest,
    generate_prepared_interview,
    get_use_case,
    list_use_cases,
    validate_request,
)

router = APIRouter(prefix="/v3/interview", tags=["Interview Questions V3"])


class InterviewUseCaseCatalog(BaseModel):
    use_cases: list[InterviewUseCase]


@router.get("/use-cases", response_model=InterviewUseCaseCatalog)
def get_interview_use_cases() -> InterviewUseCaseCatalog:
    return InterviewUseCaseCatalog(use_cases=list_use_cases())


@router.post("/questions", response_model=PreparedInterview)
@limiter.limit(AI_GENERATION_LIMIT)
def prepare_interview_questions(
    request: Request,
    response: Response,
    payload: PreparedInterviewRequest,
) -> PreparedInterview:
    """The questions someone will be asked, and answers they can give.

    No career analysis runs first. The interview type carries the preparation,
    and whatever the person supplied narrows it — which is the whole point of
    the pivot: a useful page exists even when they supply almost nothing.
    """
    definition = get_use_case(payload.use_case_id)
    if definition is None:
        raise user_facing_error(UNKNOWN_USE_CASE)

    try:
        answers = validate_request(payload, definition)
    except ValueError as exc:
        # Phrased for whoever wrote the client, so it stays in the log.
        logger.warning(
            "Interview questions rejected use_case_id=%s reason=%s",
            payload.use_case_id,
            exc,
        )
        raise user_facing_error(PREPARATION_INVALID_REQUEST) from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("Interview questions rejected reason=missing_openai_api_key")
        raise user_facing_error(SERVICE_UNAVAILABLE)

    logger.info(
        "Interview questions started use_case_id=%s answer_count=%s experience_count=%s",
        payload.use_case_id,
        len(answers),
        len(payload.experiences),
    )
    try:
        # Not named `response`: that parameter is the Response object slowapi
        # writes the rate-limit headers into.
        prepared = generate_prepared_interview(
            OpenAI(api_key=api_key),
            definition,
            answers,
            payload.experiences,
            payload.cv_text,
        )
    except Exception as exc:
        logger.exception("Interview questions failed use_case_id=%s", payload.use_case_id)
        raise user_facing_error(PREPARATION_GENERATION_FAILED) from exc

    logger.info(
        "Interview questions completed use_case_id=%s question_count=%s",
        payload.use_case_id,
        len(prepared.questions),
    )
    return prepared
