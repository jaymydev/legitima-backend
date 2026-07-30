from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from openai import OpenAI
from pydantic import BaseModel

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
def kickoff_premium_preparation(
    payload: PremiumKickoffRequest,
) -> PremiumKickoffResponse:
    """First premium deliverable, generated at purchase time.

    The client blocks on this call, so it stays deliberately small: one
    objection, one defensible answer, from the lean context alone.
    """
    if not has_usable_context(payload.context):
        raise HTTPException(
            status_code=422,
            detail="Context does not contain enough material to build an answer",
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("Premium kickoff rejected reason=missing_openai_api_key")
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY environment variable is missing")

    logger.info(
        "Premium kickoff started has_sensitive_point=%s has_freemium_analysis=%s",
        bool(payload.context.sensitive_point.strip()),
        bool(payload.context.freemium_analysis.strip()),
    )
    try:
        response = generate_kickoff(OpenAI(api_key=api_key), payload.context)
    except Exception as exc:
        logger.exception("Premium kickoff failed")
        raise HTTPException(status_code=500, detail="Premium kickoff generation failed") from exc

    logger.info("Premium kickoff completed")
    return response


@router.post("/analyze", response_model=InterviewPreparationResponse)
def analyze_interview_preparation(
    payload: InterviewPreparationRequest,
) -> InterviewPreparationResponse:
    definition = get_use_case(payload.use_case_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Unknown interview use case")

    try:
        answers = validate_request(payload, definition)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning(
            "Interview preparation rejected reason=missing_openai_api_key use_case_id=%s",
            payload.use_case_id,
        )
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY environment variable is missing")

    logger.info(
        "Interview preparation started use_case_id=%s questionnaire_version=%s answer_count=%s",
        payload.use_case_id,
        payload.questionnaire_version,
        len(answers),
    )
    try:
        response = generate_preparation(
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
        raise HTTPException(status_code=500, detail="Interview preparation generation failed") from exc

    logger.info(
        "Interview preparation completed use_case_id=%s section_count=%s",
        payload.use_case_id,
        len(response.sections),
    )
    return response
