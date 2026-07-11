from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.routes.analyze import router as analyze_router
from app.api.routes.contexte import router as contexte_router
from app.api.routes.elements import router as elements_router
from app.api.routes.fil_conducteur import router as fil_conducteur_router
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

    app.include_router(health_router)
    app.include_router(analyze_router)
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

    register_exception_handlers(app)

    @app.on_event("startup")
    def on_startup() -> None:
        logger.info("Legitima backend starting")

    return app


app = create_app()
