import json

import pytest
from fastapi.testclient import TestClient

from app.catalogo import RUTA_CATALOGO
from app.main import create_app

CATALOGO = json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))["productos"]

DEPRECATION = "@1792969200"
SUNSET = "Wed, 28 Oct 2026 23:00:00 GMT"


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app())


def _comprobar_cabeceras(respuesta, enlace: str) -> None:  # type: ignore[no-untyped-def]
    assert respuesta.headers["deprecation"] == DEPRECATION
    assert respuesta.headers["sunset"] == SUNSET
    assert respuesta.headers["link"] == f'<{enlace}>; rel="successor-version"'


# --- Historia 3: v1 obsoleta ---


def test_listado_v1_lleva_las_tres_cabeceras(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos")

    assert respuesta.status_code == 200
    _comprobar_cabeceras(respuesta, "/api/v2/productos")


def test_listado_v1_conserva_q_codificado_en_el_link(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos", params={"q": "café & té"})

    _comprobar_cabeceras(respuesta, "/api/v2/productos?q=caf%C3%A9%20%26%20t%C3%A9")


def test_detalle_v1_apunta_al_mismo_id_en_v2(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos/taza-ceramica")

    assert respuesta.status_code == 200
    _comprobar_cabeceras(respuesta, "/api/v2/productos/taza-ceramica")


def test_404_de_v1_lleva_las_cabeceras(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos/no-existe")

    assert respuesta.status_code == 404
    _comprobar_cabeceras(respuesta, "/api/v2/productos/no-existe")


def test_422_de_v1_lleva_las_cabeceras(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos", params={"q": "a" * 201})

    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": "Parámetro q no válido"}
    assert respuesta.headers["deprecation"] == DEPRECATION
    assert respuesta.headers["sunset"] == SUNSET
    assert respuesta.headers["link"].endswith('; rel="successor-version"')


def test_link_codifica_valores_con_saltos_de_linea_o_destinos_ajenos(
    cliente: TestClient,
) -> None:
    respuesta = cliente.get("/api/v1/productos/%0d%0aX-Inyectado:%20si%3E%3Chttp:malo")

    assert "x-inyectado" not in respuesta.headers
    link = respuesta.headers["link"]
    assert link.startswith("</api/v2/productos/")
    assert "\r" not in link and "\n" not in link
    assert link.count("<") == 1 and link.count(">") == 1


def test_el_cuerpo_de_v1_no_cambia_y_no_incluye_moneda(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/productos").json() == CATALOGO
    assert cliente.get("/api/v1/productos/taza-ceramica").json() == CATALOGO[2]


def test_v2_health_y_rutas_desconocidas_no_llevan_las_cabeceras(cliente: TestClient) -> None:
    for url in ("/api/v2/productos", "/api/v2/productos/taza-ceramica", "/health"):
        respuesta = cliente.get(url)
        assert "deprecation" not in respuesta.headers
        assert "sunset" not in respuesta.headers
        assert "link" not in respuesta.headers
    desconocida = cliente.get("/api/v1/otra-cosa")
    assert desconocida.status_code == 404
    assert "deprecation" not in desconocida.headers


def test_las_fechas_no_dependen_de_cuando_se_consulta(cliente: TestClient) -> None:
    primera = cliente.get("/api/v1/productos")
    segunda = cliente.get("/api/v1/productos")

    assert primera.headers["deprecation"] == segunda.headers["deprecation"] == DEPRECATION
