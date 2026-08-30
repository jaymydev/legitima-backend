from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.errors import register_user_facing_error_handler
from app.api.health import router as health_router
from app.api.rate_limit import limiter
from app.api.routes.analyze import router as analyze_router
from app.api.routes.contexte import router as contexte_router
from app.api.routes.cv import router as cv_router
from app.api.routes.elements import router as elements_router
from app.api.routes.fil_conducteur import router as fil_conducteur_router
from app.api.routes.interview_preparation import router as interview_preparation_router
from app.api.routes.interview_questions import router as interview_questions_router
from app.api.routes.question_bank import router as question_bank_router
from app.api.routes.parcours import router as parcours_router
from app.api.routes.reponses import router as reponses_router
from app.api.routes.requalifications import router as requalifications_router
from app.api.routes.zones import router as zones_router
from app.config.settings import settings
from app.observability.errors import register_exception_handlers
from app.observability.logging import configure_logging, logger


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name, version=settings.version)

    # Registered before the routers so the blanket limit covers every path,
    # including any added later without a decorator.
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.include_router(health_router)
    app.include_router(analyze_router)
    app.include_router(cv_router)
    app.include_router(interview_preparation_router)
    app.include_router(interview_questions_router)
    app.include_router(question_bank_router)
    app.include_router(contexte_router, prefix="/contexte", tags=["ContexteEntretien"])
    app.include_router(parcours_router, prefix="/parcours", tags=["ParcoursProfessionnel"])
    app.include_router(elements_router, prefix="/elements", tags=["ElementDeParcours"])
    app.include_router(zones_router, prefix="/zones", tags=["ZoneSensible"])
    app.include_router(requalifications_router, prefix="/requalifications", tags=["Requalification"])
    app.include_router(
        fil_conducteur_router,
        prefix="/fil-conducteur",
        tags=["FilConducteur"],
    )
    app.include_router(reponses_router, prefix="/reponses", tags=["ReponseEntretien"])

    register_user_facing_error_handler(app)
    register_exception_handlers(app)

    @app.on_event("startup")
    def on_startup() -> None:
        logger.info("Legitima backend starting")

    return app


app = create_app()
