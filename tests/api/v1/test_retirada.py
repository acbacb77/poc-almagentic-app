"""Spec 005: toda ruta bajo /api/v1/ responde 410 Gone con enlace a v2."""

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import create_app

DEPRECATION = "@1792969200"
SUNSET = "Wed, 28 Oct 2026 23:00:00 GMT"
METODOS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
RUTAS = [
    "/api/v1/productos",
    "/api/v1/productos/taza-ceramica",
    "/api/v1/productos/no-existe",
    "/api/v1/otra-cosa",
    "/api/v1/productos/",
    "/api/v1/productos/a/b",
]


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app())


def _enlace(destino: str) -> str:
    return f'<{destino}>; rel="successor-version"'


# --- US1: mensaje genérico y Link a v2 (FR-001, FR-002, FR-005, FR-006, FR-007) ---


def test_listado_v1_da_410_con_mensaje_generico(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos")

    assert respuesta.status_code == 410
    assert list(respuesta.json()) == ["detail"]
    assert isinstance(respuesta.json()["detail"], str)


@pytest.mark.parametrize("id_", ["taza-ceramica", "no-existe"])
def test_detalle_v1_da_410_exista_o_no_el_id(cliente: TestClient, id_: str) -> None:
    respuesta = cliente.get(f"/api/v1/productos/{id_}")

    assert respuesta.status_code == 410
    assert respuesta.headers["link"] == _enlace(f"/api/v2/productos/{id_}")


def test_410_lleva_deprecation_sunset_y_link(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos")

    assert respuesta.headers["deprecation"] == DEPRECATION
    assert respuesta.headers["sunset"] == SUNSET
    assert respuesta.headers["link"] == _enlace("/api/v2/productos")


def test_el_link_conserva_q_codificado(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos", params={"q": "café & té"})

    assert respuesta.status_code == 410
    assert respuesta.headers["link"] == _enlace("/api/v2/productos?q=caf%C3%A9%20%26%20t%C3%A9")


def test_con_q_repetido_el_link_usa_el_ultimo_valor(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos?q=taza&q=molinillo")

    assert respuesta.headers["link"] == _enlace("/api/v2/productos?q=molinillo")


# --- US2: ningún método ni ruta escapa al 410 (FR-001, FR-003, FR-010) ---


@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("ruta", RUTAS)
def test_todos_los_metodos_y_rutas_dan_410_con_las_mismas_cabeceras(
    cliente: TestClient, metodo: str, ruta: str
) -> None:
    respuesta = cliente.request(metodo, ruta)

    assert respuesta.status_code == 410
    assert respuesta.headers["deprecation"] == DEPRECATION
    assert respuesta.headers["sunset"] == SUNSET
    assert respuesta.headers["link"] == _enlace(ruta.replace("/api/v1/", "/api/v2/", 1))
    if metodo == "HEAD":
        assert respuesta.content == b""


def test_ruta_inexistente_da_410_y_no_404(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/otra-cosa").status_code == 410


def test_parametros_invalidos_dan_410_y_no_422(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos", params={"q": "a" * 201})

    assert respuesta.status_code == 410


def test_el_cuerpo_no_repite_lo_recibido(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos/secreto-123", params={"q": "texto-privado"})

    assert "secreto-123" not in respuesta.text
    assert "texto-privado" not in respuesta.text
    assert "productos" not in respuesta.text


def test_el_cuerpo_no_incluye_datos_del_catalogo(cliente: TestClient) -> None:
    assert "taza" not in cliente.get("/api/v1/productos").text


def test_link_codifica_saltos_de_linea_y_destinos_ajenos(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos/%0d%0aX-Inyectado:%20si%3E%3Chttp:malo")

    assert "x-inyectado" not in respuesta.headers
    link = respuesta.headers["link"]
    assert link.startswith("</api/v2/productos/")
    assert "\r" not in link and "\n" not in link
    assert link.count("<") == 1 and link.count(">") == 1


def test_las_fechas_no_dependen_de_cuando_se_consulta(cliente: TestClient) -> None:
    primera = cliente.get("/api/v1/productos")
    segunda = cliente.get("/api/v1/productos")

    assert primera.headers["deprecation"] == segunda.headers["deprecation"] == DEPRECATION


@pytest.mark.parametrize("ruta", ["/api/v10/productos", "/api/v1x"])
def test_prefijos_parecidos_no_son_v1(cliente: TestClient, ruta: str) -> None:
    respuesta = cliente.get(ruta)

    assert respuesta.status_code == 404
    assert "deprecation" not in respuesta.headers
    assert "link" not in respuesta.headers


# --- FR-008: no se cachea ---


def test_el_410_no_se_cachea(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/productos").headers["cache-control"] == "no-store"


# --- US3: v2 y /health no cambian (FR-009) ---


@pytest.mark.parametrize("url", ["/api/v2/productos", "/api/v2/productos/taza-ceramica", "/health"])
def test_v2_y_health_no_llevan_cabeceras_de_retirada(cliente: TestClient, url: str) -> None:
    respuesta = cliente.get(url)

    assert respuesta.status_code == 200
    for cabecera in ("deprecation", "sunset", "link"):
        assert cabecera not in respuesta.headers


# --- US4: métricas (FR-011, FR-012) ---


def _consultas(metodo: str, ruta: str, estado: str) -> float:
    etiquetas = {"metodo": metodo, "ruta": ruta, "estado": estado}
    return REGISTRY.get_sample_value("app_consultas_total", etiquetas) or 0.0


def test_las_metricas_cuentan_v1_siempre_con_410(cliente: TestClient) -> None:
    plantilla = "/api/v1/{ruta:resto}"
    antes = _consultas("GET", plantilla, "410")

    cliente.get("/api/v1/productos")
    cliente.get("/api/v1/productos/uno")
    cliente.get("/api/v1/productos", params={"q": "a" * 201})

    assert _consultas("GET", plantilla, "410") == antes + 3


def test_las_metricas_no_crean_series_por_ruta_ni_valor(cliente: TestClient) -> None:
    def series() -> int:
        return sum(
            1
            for familia in REGISTRY.collect()
            if familia.name == "app_consultas"
            for muestra in familia.samples
            if muestra.name == "app_consultas_total" and "/api/v1/" in muestra.labels["ruta"]
        )

    cliente.get("/api/v1/productos")
    antes = series()
    for i in range(5):
        cliente.get(f"/api/v1/valor-{i}/x", params={"q": f"q{i}"})

    assert series() == antes


def test_los_logs_no_incluyen_la_ruta_recibida(
    cliente: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("INFO", logger="app.consultas"):
        cliente.get("/api/v1/productos/ana@example.com", params={"q": "secreto"})

    registro = " ".join(r.getMessage() for r in caplog.records if r.name == "app.consultas")
    assert "410" in registro
    assert "ana@example.com" not in registro
    assert "secreto" not in registro


# --- US5: documentación (FR-016) ---


def test_openapi_no_publica_v1(cliente: TestClient) -> None:
    rutas = cliente.get("/openapi.json").json()["paths"]

    assert not any(ruta.startswith("/api/v1") for ruta in rutas)
    assert "/api/v2/productos" in rutas
