"""The errors that reach someone's screen, and the codes that identify them.

The iOS client shows a failed request's `detail` verbatim, in red, to someone
who is preparing for a job interview. So `detail` is French prose written for
that person: what happened, and what to do next. Nothing internal goes in it —
the reason belongs in the log, where it helps and where it cannot leak.

Alongside it, `code` is the stable half of the contract. Rewording a sentence
must never break a client, and a client that wants its own phrasing keys off
the code instead of matching on the sentence. Holding every message in one
table also means the wording can be reviewed in one place.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

SERVICE_UNAVAILABLE = "service_unavailable"
INVALID_REQUEST = "invalid_request"

CV_UNSUPPORTED_FILE_TYPE = "cv_unsupported_file_type"
CV_FILE_TOO_LARGE = "cv_file_too_large"
CV_IMAGE_UNREADABLE = "cv_image_unreadable"
CV_IMAGE_NO_TEXT = "cv_image_no_text"
CV_OCR_UNAVAILABLE = "cv_ocr_unavailable"
CV_PDF_EXPECTED = "cv_pdf_expected"
CV_PDF_UNREADABLE = "cv_pdf_unreadable"
CV_PDF_NO_TEXT = "cv_pdf_no_text"
CV_NO_EXPERIENCES = "cv_no_experiences"

ANALYSIS_GENERATION_FAILED = "analysis_generation_failed"
ANALYSIS_INVALID_MODEL_RESPONSE = "analysis_invalid_model_response"
ANALYSIS_QUALITY_INSUFFICIENT = "analysis_quality_insufficient"

PREPARATION_CONTEXT_TOO_THIN = "preparation_context_too_thin"
PREPARATION_INVALID_REQUEST = "preparation_invalid_request"
PREPARATION_GENERATION_FAILED = "preparation_generation_failed"
KICKOFF_GENERATION_FAILED = "kickoff_generation_failed"
UNKNOWN_USE_CASE = "unknown_use_case"

_RETRY_LATER = "Réessayez dans quelques instants."

#: code -> (HTTP status, French sentence shown to the user as written)
_CATALOG: dict[str, tuple[int, str]] = {
    SERVICE_UNAVAILABLE: (
        500,
        f"Le service est momentanément indisponible. {_RETRY_LATER}",
    ),
    INVALID_REQUEST: (
        422,
        "La demande envoyée n'a pas pu être traitée. "
        "Mettez l'application à jour, puis réessayez.",
    ),
    CV_UNSUPPORTED_FILE_TYPE: (
        415,
        "Ce format de fichier n'est pas pris en charge. "
        "Importez votre CV en PDF, en JPEG ou en PNG.",
    ),
    CV_FILE_TOO_LARGE: (
        413,
        "Ce fichier dépasse {max_megabytes} Mo. "
        "Importez une version plus légère de votre CV.",
    ),
    CV_IMAGE_UNREADABLE: (
        422,
        "Cette image n'a pas pu être ouverte. "
        "Vérifiez qu'il s'agit bien d'une photo de votre CV, puis réessayez.",
    ),
    CV_IMAGE_NO_TEXT: (
        422,
        "Aucun texte n'a pu être lu sur cette photo. "
        "Reprenez-la à plat, bien éclairée et sans reflet, "
        "ou importez votre CV en PDF.",
    ),
    CV_OCR_UNAVAILABLE: (
        500,
        "La lecture des photos est momentanément indisponible. "
        "Importez votre CV en PDF, ou réessayez plus tard.",
    ),
    CV_PDF_EXPECTED: (
        422,
        "Ce format ne peut pas être lu ici. "
        "Importez votre CV dans un PDF au format texte.",
    ),
    CV_PDF_UNREADABLE: (
        422,
        "Ce PDF n'a pas pu être ouvert. "
        "Vérifiez qu'il n'est pas protégé par un mot de passe, puis réessayez.",
    ),
    CV_PDF_NO_TEXT: (
        422,
        "Aucun texte n'a pu être extrait de ce PDF. C'est probablement un scan : "
        "importez-le comme photo, ou utilisez un PDF au format texte.",
    ),
    CV_NO_EXPERIENCES: (
        422,
        "Aucune expérience professionnelle exploitable n'a été trouvée dans ce "
        "document. Vérifiez qu'il s'agit bien d'un CV, et qu'il est lisible.",
    ),
    ANALYSIS_GENERATION_FAILED: (
        500,
        f"L'analyse n'a pas pu être produite. {_RETRY_LATER}",
    ),
    # The model answered with something its own schema rejects. That is our
    # fault, not the caller's; the 422 is kept only because changing a status
    # code shipped in 1.0 would be a separate decision.
    ANALYSIS_INVALID_MODEL_RESPONSE: (
        422,
        f"L'analyse n'a pas pu être produite. {_RETRY_LATER}",
    ),
    ANALYSIS_QUALITY_INSUFFICIENT: (
        500,
        "L'analyse produite n'atteignait pas le niveau de qualité attendu. "
        f"{_RETRY_LATER}",
    ),
    PREPARATION_CONTEXT_TOO_THIN: (
        422,
        "Votre parcours ne contient pas encore assez d'éléments pour préparer "
        "une réponse. Complétez-le, puis relancez la préparation.",
    ),
    PREPARATION_INVALID_REQUEST: (
        422,
        "Cette demande de préparation n'a pas pu être traitée. "
        "Mettez l'application à jour, puis réessayez.",
    ),
    PREPARATION_GENERATION_FAILED: (
        500,
        f"La préparation n'a pas pu être produite. {_RETRY_LATER}",
    ),
    KICKOFF_GENERATION_FAILED: (
        500,
        f"La préparation n'a pas pu être produite. {_RETRY_LATER}",
    ),
    UNKNOWN_USE_CASE: (
        404,
        "Ce type d'entretien n'est pas reconnu. "
        "Mettez l'application à jour, puis réessayez.",
    ),
}


class UserFacingError(HTTPException):
    """An HTTP error whose `detail` is displayed to someone, as written."""

    def __init__(self, *, status_code: int, code: str, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.code = code


def user_facing_error(code: str, **fields: object) -> UserFacingError:
    """Build the error for `code`, filling any placeholder in its sentence."""
    status_code, template = _CATALOG[code]
    return UserFacingError(
        status_code=status_code,
        code=code,
        detail=template.format(**fields) if fields else template,
    )


def register_user_facing_error_handler(app: FastAPI) -> None:
    """Emit `{"detail": ..., "code": ...}` instead of FastAPI's `{"detail": ...}`.

    `detail` keeps its shape and its position, so a client that only reads it —
    every client shipped so far — needs no change to benefit from this.
    """

    @app.exception_handler(UserFacingError)
    async def handle_user_facing_error(
        request: Request,
        exc: UserFacingError,
    ) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """The last English sentence that could reach a screen.

        FastAPI answers a malformed body with `detail` as a list of
        `{"msg": "Field required"}`, and the client reads the first `msg` — so a
        client bug reads, in French, as English. It takes a client bug to get
        here, but this repository has already shipped one: re-adding
        `from __future__ import annotations` to the interview preparation router
        downgrades its body to a query parameter and answers every POST with
        exactly this. The offending fields move to `fields`, where they stay
        available to whoever is debugging the client.
        """
        del request
        status_code, detail = _CATALOG[INVALID_REQUEST]
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": detail,
                "code": INVALID_REQUEST,
                "fields": [
                    ".".join(str(part) for part in error.get("loc", ()))
                    for error in exc.errors()
                ],
            },
        )
