"""Spec 006: log de acceso sin la ruta de v1 y 410 en /api/v1 sin barra final."""

import logging

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.api.v1.productos import DEPRECATION, SUNSET
from app.main import create_app
from app.observabilidad import MARCADOR_V1, SinRutaV1

METODOS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app(), follow_redirects=False)


def _acceso(caplog: pytest.LogCaptureFixture, ruta: str, estado: int = 410) -> str:
    """Emite una línea de acceso como uvicorn y devuelve el mensaje ya filtrado."""
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="uvicorn.access"):
        logging.getLogger("uvicorn.access").info(
            '%s - "%s %s HTTP/%s" %d', "127.0.0.1:1234", "GET", ruta, "1.1", estado
        )
    return next(r.getMessage() for r in caplog.records if r.name == "uvicorn.access")


# --- US1: log de acceso (FR-001 a FR-005) ---


@pytest.mark.parametrize(
    "ruta",
    [
        "/api/v1/productos/valor-secreto-123?q=dato-privado",
        "/api/v1/otra-cosa/xyz",
        "/api/v1/productos/a/b",
        "/api/v1/productos/",
        "/api/v1/%2e%2e/x",
        "/api/v1",
        "/api/v1?q=dato-privado",
        "/api/%76%31/valor-secreto-123",
    ],
)
def test_el_log_de_v1_lleva_el_marcador_y_nada_de_lo_recibido(
    caplog: pytest.LogCaptureFixture, ruta: str
) -> None:
    create_app()

    mensaje = _acceso(caplog, ruta)

    assert mensaje == f'127.0.0.1:1234 - "GET {MARCADOR_V1} HTTP/1.1" 410'


def test_el_marcador_es_el_fijado_por_la_spec() -> None:
    assert MARCADOR_V1 == "/api/v1/[retirada]"


# --- US3: nada más cambia (FR-004, FR-009, FR-012) ---


@pytest.mark.parametrize(
    "ruta",
    ["/api/v2/productos", "/api/v2/productos/taza-ceramica", "/health", "/api/v10/productos"],
)
def test_otras_rutas_se_registran_como_antes(caplog: pytest.LogCaptureFixture, ruta: str) -> None:
    create_app()

    mensaje = _acceso(caplog, ruta, 200)

    assert mensaje == f'127.0.0.1:1234 - "GET {ruta} HTTP/1.1" 200'


def test_v2_sigue_quitando_solo_la_query_string(caplog: pytest.LogCaptureFixture) -> None:
    create_app()

    mensaje = _acceso(caplog, "/api/v2/productos?q=secreto", 200)

    assert mensaje == '127.0.0.1:1234 - "GET /api/v2/productos HTTP/1.1" 200'


def test_el_filtro_de_ruta_v1_no_se_duplica() -> None:
    create_app()
    create_app()

    filtros = logging.getLogger("uvicorn.access").filters
    assert sum(isinstance(f, SinRutaV1) for f in filtros) == 1


# --- US2: /api/v1 sin barra (FR-006 a FR-008, FR-010) ---


@pytest.mark.parametrize("metodo", METODOS)
def test_api_v1_sin_barra_da_410_con_las_tres_cabeceras(cliente: TestClient, metodo: str) -> None:
    respuesta = cliente.request(metodo, "/api/v1")

    assert respuesta.status_code == 410
    assert respuesta.headers["deprecation"] == DEPRECATION
    assert respuesta.headers["sunset"] == SUNSET
    assert respuesta.headers["link"] == '</api/v2>; rel="successor-version"'
    assert respuesta.headers["cache-control"] == "no-store"
    assert "location" not in respuesta.headers
    if metodo == "HEAD":
        assert respuesta.content == b""
    else:
        assert list(respuesta.json()) == ["detail"]


def test_api_v1_sin_barra_con_query_conserva_q_en_el_link(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1", params={"q": "taza", "otro": "dato-privado"})

    assert respuesta.status_code == 410
    assert respuesta.headers["link"] == '</api/v2?q=taza>; rel="successor-version"'
    assert "dato-privado" not in respuesta.text


def test_api_v1_sin_barra_se_cuenta_como_v1_con_410(cliente: TestClient) -> None:
    def total() -> float:
        etiquetas = {"metodo": "GET", "ruta": "/api/v1", "estado": "410"}
        return REGISTRY.get_sample_value("app_consultas_total", etiquetas) or 0.0

    antes = total()
    cliente.get("/api/v1", params={"q": "valor-unico-1"})
    cliente.get("/api/v1", params={"q": "valor-unico-2"})

    assert total() == antes + 2


@pytest.mark.parametrize("ruta", ["/api/v10", "/api/v1x"])
def test_prefijos_parecidos_sin_barra_siguen_en_404(cliente: TestClient, ruta: str) -> None:
    respuesta = cliente.get(ruta)

    assert respuesta.status_code == 404
    assert "deprecation" not in respuesta.headers


def test_redirect_slashes_de_v2_no_cambia(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v2/productos/")

    assert respuesta.status_code == 307
    assert respuesta.headers["location"].endswith("/api/v2/productos")


# --- US4: métricas y logs propios (FR-011) ---


def test_metricas_y_logs_propios_no_incluyen_lo_recibido(
    cliente: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="app.consultas"):
        cliente.get("/api/v1/productos/valor-secreto-123", params={"q": "dato-privado"})
        cliente.get("/api/v1", params={"q": "dato-privado"})

    registro = " ".join(r.getMessage() for r in caplog.records if r.name == "app.consultas")
    metricas = " ".join(
        str(m.labels) for f in REGISTRY.collect() if f.name == "app_consultas" for m in f.samples
    )
    for texto in ("valor-secreto-123", "dato-privado"):
        assert texto not in registro
        assert texto not in metricas
    assert "410" in registro
