import os
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from starlette.middleware.base import RequestResponseEndpoint

from app.api.v1 import productos
from app.api.v2 import productos as productos_v2
from app.catalogo import RUTA_CATALOGO, cargar_catalogo
from app.observabilidad import configurar_logs, iniciar_metricas, registrar_consulta


async def sin_cache(request: Request, call_next: RequestResponseEndpoint) -> Response:
    respuesta = await call_next(request)
    # FR-009: ninguna respuesta del catálogo (404 incluido) se guarda en cachés.
    if request.url.path.startswith("/api/"):
        respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


# Fechas fijas de la spec 004 (FR-012): RFC 9745 (Deprecation) y RFC 8594 (Sunset).
DEPRECATION = "@1792969200"
SUNSET = "Wed, 28 Oct 2026 23:00:00 GMT"
RUTA_LISTADO_V1 = "/api/v1/productos"
RUTA_DETALLE_V1 = "/api/v1/productos/{id}"


async def aviso_obsolescencia_v1(request: Request, call_next: RequestResponseEndpoint) -> Response:
    respuesta = await call_next(request)
    # La ruta casada también existe en las respuestas de error (404, 422) de v1.
    ruta = getattr(request.scope.get("route"), "path", "")
    if ruta == RUTA_LISTADO_V1:
        destino = "/api/v2/productos"
        if "q" in request.query_params:
            destino += "?q=" + quote(request.query_params["q"], safe="")
    elif ruta == RUTA_DETALLE_V1:
        destino = "/api/v2/productos/" + quote(str(request.path_params["id"]), safe="")
    else:
        return respuesta
    respuesta.headers["Deprecation"] = DEPRECATION
    respuesta.headers["Sunset"] = SUNSET
    respuesta.headers["Link"] = f'<{destino}>; rel="successor-version"'
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
    app.middleware("http")(aviso_obsolescencia_v1)

    @app.get("/health")
    def health() -> EstadoSalud:
        return EstadoSalud(status="ok")

    app.include_router(productos.router)
    app.include_router(productos_v2.router)

    return app


app = create_app()
