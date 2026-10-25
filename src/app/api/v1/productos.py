"""API v1 retirada (spec 005): toda ruta bajo /api/v1/ responde 410 Gone."""

from urllib.parse import quote

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from starlette.convertors import StringConvertor, register_url_convertor


class _RestoDeRuta(StringConvertor):
    """Como `path`, pero también casa saltos de línea: ninguna ruta de v1 escapa al 410."""

    regex = r"[\s\S]*"


register_url_convertor("resto", _RestoDeRuta())

router = APIRouter(prefix="/api/v1", tags=["v1 (retirada)"])

# Fechas fijas de la spec 004 (FR-010 y FR-012): RFC 9745 (Deprecation) y RFC 8594 (Sunset).
DEPRECATION = "@1792969200"
SUNSET = "Wed, 28 Oct 2026 23:00:00 GMT"
MENSAJE = "Este recurso ha sido retirado"
METODOS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


def _enlace_v2(request: Request) -> str:
    # Mismo path con v1 → v2; lo recibido se codifica para no inyectar cabeceras ni destinos.
    # `/api/v1` sin barra no tiene parámetro de ruta: su destino es `/api/v2` (spec 006, FR-008).
    if "ruta" in request.path_params:
        destino = "/api/v2/" + quote(request.path_params["ruta"], safe="/")
    else:
        destino = "/api/v2"
    if "q" in request.query_params:
        destino += "?q=" + quote(request.query_params["q"], safe="")
    return f'<{destino}>; rel="successor-version"'


# Una sola ruta comodín: así v1 no valida nada (ni 404, ni 405, ni 422) y la plantilla
# registrada en las métricas es siempre la misma (cardinalidad acotada).
# No se publica en OpenAPI (FR-016).
# La ruta "" cubre `/api/v1` sin barra final (spec 006): se resuelve aquí, sin tocar
# redirect_slashes, que sigue igual para el resto de rutas.
@router.api_route("", methods=METODOS, include_in_schema=False)
@router.api_route("/{ruta:resto}", methods=METODOS, include_in_schema=False)
def retirada(request: Request) -> Response:
    cabeceras = {
        "Deprecation": DEPRECATION,
        "Sunset": SUNSET,
        "Link": _enlace_v2(request),
    }
    if request.method == "HEAD":
        return Response(status_code=410, headers=cabeceras)
    return JSONResponse({"detail": MENSAJE}, status_code=410, headers=cabeceras)
