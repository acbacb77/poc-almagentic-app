import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.catalogo import RUTA_CATALOGO
from app.main import create_app

CATALOGO = json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))["productos"]


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app())


# --- Historia 1: consultar el catálogo completo ---


def test_listado_devuelve_el_catalogo_completo(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos")

    assert respuesta.status_code == 200
    assert respuesta.json() == CATALOGO


def test_listado_incluye_exactamente_id_nombre_y_precio(cliente: TestClient) -> None:
    productos = cliente.get("/api/v1/productos").json()

    assert 5 <= len(productos) <= 10
    for producto in productos:
        assert set(producto) == {"id", "nombre", "precio"}


def test_listado_se_atiende_sin_credenciales(cliente: TestClient) -> None:
    assert "authorization" not in cliente.headers

    respuesta = cliente.get("/api/v1/productos")

    assert respuesta.status_code == 200


def test_listado_expresa_el_precio_con_exactamente_2_decimales(cliente: TestClient) -> None:
    for producto in cliente.get("/api/v1/productos").json():
        assert isinstance(producto["precio"], str)
        assert re.fullmatch(r"\d+\.\d{2}", producto["precio"])


def test_dos_consultas_seguidas_devuelven_lo_mismo_y_en_el_mismo_orden(
    cliente: TestClient,
) -> None:
    primera = cliente.get("/api/v1/productos").json()
    segunda = cliente.get("/api/v1/productos").json()

    assert primera == segunda
    assert [p["id"] for p in primera] == [p["id"] for p in CATALOGO]


# --- Historia 2: consultar un producto por su identificador ---


def test_producto_existente_coincide_con_el_listado(cliente: TestClient) -> None:
    for esperado in cliente.get("/api/v1/productos").json():
        respuesta = cliente.get(f"/api/v1/productos/{esperado['id']}")

        assert respuesta.status_code == 200
        assert respuesta.json() == esperado


def test_producto_inexistente_responde_404_generico(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos/no-existe")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Producto no encontrado"}


@pytest.mark.parametrize(
    "identificador",
    [
        "0",
        "-1",
        "12345",
        "CAFE-MOLIDO-250G",
        "cafe-molido-250g ",
        "%3Cscript%3E",
        "ñ-€-✓",
        "null",
        "a" * 5000,
    ],
)
def test_cualquier_identificador_desconocido_responde_el_mismo_404(
    cliente: TestClient, identificador: str
) -> None:
    respuesta = cliente.get(f"/api/v1/productos/{identificador}")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Producto no encontrado"}


@pytest.mark.parametrize("ruta", ["..%2F..%2Fetc%2Fpasswd", "a/b", "cafe-molido-250g/extra"])
def test_una_ruta_con_barras_responde_404_generico(cliente: TestClient, ruta: str) -> None:
    # Con barras ya no es un identificador: responde el 404 del framework,
    # con la misma forma {"detail": "..."} y sin detalles internos.
    respuesta = cliente.get(f"/api/v1/productos/{ruta}")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Not Found"}


# --- Historia 3: ver un precio actualizado tras un despliegue ---


def test_tras_desplegar_un_cambio_de_precio_se_devuelve_el_precio_nuevo(tmp_path: Path) -> None:
    id_producto = CATALOGO[0]["id"]
    assert CATALOGO[0]["precio"] != "99.99"
    antes = TestClient(create_app())
    assert antes.get(f"/api/v1/productos/{id_producto}").json()["precio"] == CATALOGO[0]["precio"]

    modificado = [{**CATALOGO[0], "precio": "99.99"}, *CATALOGO[1:]]
    ruta = tmp_path / "catalogo.json"
    ruta.write_text(json.dumps({"productos": modificado}), encoding="utf-8")
    despues = TestClient(create_app(ruta))

    assert despues.get("/api/v1/productos").json()[0]["precio"] == "99.99"
    assert despues.get(f"/api/v1/productos/{id_producto}").json()["precio"] == "99.99"


def test_las_respuestas_no_piden_al_cliente_que_las_cachee(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/productos")

    assert "cache-control" not in respuesta.headers
    assert "etag" not in respuesta.headers
