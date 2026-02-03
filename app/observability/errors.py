from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.observability.logging import logger


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={"message": "internal server error"},
        )
