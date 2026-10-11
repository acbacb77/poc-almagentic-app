import json
import logging
import sys
import time

from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger("app.consultas")

CONSULTAS = Counter(
    "app_consultas_total",
    "Consultas atendidas por la API",
    ["metodo", "ruta", "estado"],
)
DURACION = Histogram(
    "app_consulta_duracion_segundos",
    "Duración de las consultas atendidas por la API",
    ["metodo", "ruta"],
)
BUSQUEDAS = Counter(
    "app_busquedas_total",
    "Búsquedas de productos por nombre",
    ["resultado"],
)


def registrar_busqueda(longitud_q: int, resultados: int) -> None:
    """Deja traza de una búsqueda sin el texto buscado, que lo escribe la persona usuaria."""
    BUSQUEDAS.labels("con_resultados" if resultados else "sin_resultados").inc()
    logger.info(
        json.dumps({"evento": "busqueda", "longitud_q": longitud_q, "resultados": resultados})
    )


class SinQueryString(logging.Filter):
    """Quita la query string de la ruta en el log de acceso de uvicorn (FR-011)."""

    def filter(self, record: logging.LogRecord) -> bool:
        # uvicorn.access registra args = (cliente, método, ruta con query, versión, estado).
        if isinstance(record.args, tuple) and len(record.args) >= 3:
            ruta = record.args[2]
            if isinstance(ruta, str) and "?" in ruta:
                record.args = (*record.args[:2], ruta.split("?", 1)[0], *record.args[3:])
        return True


def configurar_logs() -> None:
    acceso = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, SinQueryString) for f in acceso.filters):
        acceso.addFilter(SinQueryString())
    raiz = logging.getLogger("app")
    if not raiz.handlers:
        salida = logging.StreamHandler(sys.stdout)
        salida.setFormatter(logging.Formatter("%(message)s"))
        raiz.addHandler(salida)
    raiz.setLevel(logging.INFO)


async def registrar_consulta(request: Request, call_next: RequestResponseEndpoint) -> Response:
    inicio = time.perf_counter()
    estado = 500
    try:
        respuesta = await call_next(request)
        estado = respuesta.status_code
        return respuesta
    finally:
        # Se registra la plantilla de la ruta, nunca la URL recibida: sin datos
        # del cliente en los logs y sin cardinalidad libre en las métricas.
        ruta = getattr(request.scope.get("route"), "path", "")
        if ruta.startswith("/api/"):
            duracion = time.perf_counter() - inicio
            CONSULTAS.labels(request.method, ruta, str(estado)).inc()
            DURACION.labels(request.method, ruta).observe(duracion)
            logger.info(
                json.dumps(
                    {
                        "evento": "consulta",
                        "metodo": request.method,
                        "ruta": ruta,
                        "estado": estado,
                        "duracion_ms": round(duracion * 1000, 3),
                    }
                )
            )
