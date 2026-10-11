from pathlib import Path

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel
from starlette.middleware.base import RequestResponseEndpoint

from app.api.v1 import productos
from app.catalogo import RUTA_CATALOGO, cargar_catalogo
from app.observabilidad import configurar_logs, registrar_consulta


async def sin_cache(request: Request, call_next: RequestResponseEndpoint) -> Response:
    respuesta = await call_next(request)
    # FR-009: ninguna respuesta del catálogo (404 incluido) se guarda en cachés.
    if request.url.path.startswith("/api/"):
        respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


class EstadoSalud(BaseModel):
    status: str


def create_app(ruta_catalogo: Path = RUTA_CATALOGO) -> FastAPI:
    configurar_logs()
    app = FastAPI(title="poc-almagentic-app")
    # Un catálogo mal formado impide arrancar: nunca llega a servirse (FR-010).
    app.state.catalogo = cargar_catalogo(ruta_catalogo)
    app.middleware("http")(registrar_consulta)
    app.middleware("http")(sin_cache)

    @app.get("/health")
    def health() -> EstadoSalud:
        return EstadoSalud(status="ok")

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(productos.router)

    return app


app = create_app()
