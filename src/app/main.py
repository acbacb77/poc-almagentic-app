import os
from pathlib import Path

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from starlette.middleware.base import RequestResponseEndpoint

from app.api.v1 import productos as productos_v1
from app.api.v2 import productos as productos_v2
from app.catalogo import RUTA_CATALOGO, cargar_catalogo
from app.observabilidad import configurar_logs, iniciar_metricas, registrar_consulta


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
    # Las métricas van en su propio puerto (METRICS_PORT), fuera de la API pública.
    if puerto := os.environ.get("METRICS_PORT"):
        if not puerto.isdigit() or not 0 < int(puerto) < 65536:
            raise ValueError(f"METRICS_PORT debe ser un puerto entre 1 y 65535, no {puerto!r}")
        iniciar_metricas(int(puerto))
    app = FastAPI(title="poc-almagentic-app")
    # Un catálogo mal formado impide arrancar: nunca llega a servirse (FR-010).
    app.state.catalogo = cargar_catalogo(ruta_catalogo)
    app.middleware("http")(registrar_consulta)
    app.middleware("http")(sin_cache)

    @app.get("/health")
    def health() -> EstadoSalud:
        return EstadoSalud(status="ok")

    app.include_router(productos_v1.router)
    app.include_router(productos_v2.router)

    return app


app = create_app()
