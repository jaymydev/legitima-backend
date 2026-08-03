# Deliberately no `from __future__ import annotations` here. Under postponed
# evaluation FastAPI cannot resolve the body model through slowapi's decorator
# wrapper, and silently downgrades `payload` to a query parameter — every POST
# then answers 422. The annotations below need no forward references.

import os

from fastapi import APIRouter, Request, Response
from openai import OpenAI
from pydantic import BaseModel

from app.api.errors import (
    KICKOFF_GENERATION_FAILED,
    PREPARATION_CONTEXT_TOO_THIN,
    PREPARATION_GENERATION_FAILED,
    PREPARATION_INVALID_REQUEST,
    SERVICE_UNAVAILABLE,
    UNKNOWN_USE_CASE,
    user_facing_error,
)
from app.api.rate_limit import AI_GENERATION_LIMIT, limiter
from app.observability.logging import logger
from app.services.interview_preparation import (
    InterviewPreparationRequest,
    InterviewPreparationResponse,
    InterviewUseCase,
    PremiumKickoffRequest,
    PremiumKickoffResponse,
    generate_kickoff,
    generate_preparation,
    get_use_case,
    has_usable_context,
    list_use_cases,
    validate_request,
)

router = APIRouter(prefix="/v2/interview-preparation", tags=["Interview Preparation V2"])


class InterviewUseCaseCatalog(BaseModel):
    use_cases: list[InterviewUseCase]


@router.get("/use-cases", response_model=InterviewUseCaseCatalog)
def get_interview_use_cases() -> InterviewUseCaseCatalog:
    return InterviewUseCaseCatalog(use_cases=list_use_cases())


@router.post("/kickoff", response_model=PremiumKickoffResponse)
@limiter.limit(AI_GENERATION_LIMIT)
def kickoff_premium_preparation(
    request: Request,
    response: Response,
    payload: PremiumKickoffRequest,
) -> PremiumKickoffResponse:
    """First premium deliverable, generated at purchase time.

    The client blocks on this call, so it stays deliberately small: one
    objection, one defensible answer, from the lean context alone.
    """
    if not has_usable_context(payload.context):
        raise user_facing_error(PREPARATION_CONTEXT_TOO_THIN)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("Premium kickoff rejected reason=missing_openai_api_key")
        raise user_facing_error(SERVICE_UNAVAILABLE)

    logger.info(
        "Premium kickoff started has_sensitive_point=%s has_freemium_analysis=%s",
        bool(payload.context.sensitive_point.strip()),
        bool(payload.context.freemium_analysis.strip()),
    )
    try:
        # Not named `response`: that parameter is the Response object slowapi
        # writes the rate-limit headers into, and rebinding it here would hand
        # slowapi a Pydantic model instead.
        kickoff = generate_kickoff(OpenAI(api_key=api_key), payload.context)
    except Exception as exc:
        logger.exception("Premium kickoff failed")
        raise user_facing_error(KICKOFF_GENERATION_FAILED) from exc

    logger.info("Premium kickoff completed")
    return kickoff


@router.post("/analyze", response_model=InterviewPreparationResponse)
@limiter.limit(AI_GENERATION_LIMIT)
def analyze_interview_preparation(
    request: Request,
    response: Response,
    payload: InterviewPreparationRequest,
) -> InterviewPreparationResponse:
    definition = get_use_case(payload.use_case_id)
    if definition is None:
        raise user_facing_error(UNKNOWN_USE_CASE)

    try:
        answers = validate_request(payload, definition)
    except ValueError as exc:
        # These say things like "Duplicate question_id: x" — a client-contract
        # violation, phrased for whoever wrote the client. The person waiting on
        # the screen can do nothing with it, so it stays in the log.
        logger.warning(
            "Interview preparation rejected use_case_id=%s reason=%s",
            payload.use_case_id,
            exc,
        )
        raise user_facing_error(PREPARATION_INVALID_REQUEST) from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning(
            "Interview preparation rejected reason=missing_openai_api_key use_case_id=%s",
            payload.use_case_id,
        )
        raise user_facing_error(SERVICE_UNAVAILABLE)

    logger.info(
        "Interview preparation started use_case_id=%s questionnaire_version=%s answer_count=%s",
        payload.use_case_id,
        payload.questionnaire_version,
        len(answers),
    )
    try:
        # See the kickoff handler: `response` belongs to slowapi.
        preparation = generate_preparation(
            OpenAI(api_key=api_key),
            definition,
            answers,
            payload.context,
        )
    except Exception as exc:
        logger.exception(
            "Interview preparation failed use_case_id=%s questionnaire_version=%s",
            payload.use_case_id,
            payload.questionnaire_version,
        )
        raise user_facing_error(PREPARATION_GENERATION_FAILED) from exc

    logger.info(
        "Interview preparation completed use_case_id=%s section_count=%s",
        payload.use_case_id,
        len(preparation.sections),
    )
    return preparation
