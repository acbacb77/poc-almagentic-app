import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.catalogo import RUTA_CATALOGO
from app.main import create_app

CATALOGO = json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))["productos"]
PRIMERO = CATALOGO[0]


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app())


def _v2(producto: dict[str, str]) -> dict[str, object]:
    return {
        "id": producto["id"],
        "nombre": producto["nombre"],
        "precio": {"importe": producto["precio"], "moneda": "EUR"},
    }


# --- Historia 1: catálogo v2 ---


def test_listado_v2_devuelve_precio_con_importe_y_moneda(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v2/productos")

    assert respuesta.status_code == 200
    assert respuesta.json() == [_v2(p) for p in CATALOGO]


def test_detalle_v2_coincide_con_el_listado(cliente: TestClient) -> None:
    respuesta = cliente.get(f"/api/v2/productos/{PRIMERO['id']}")

    assert respuesta.status_code == 200
    assert respuesta.json() == _v2(PRIMERO)


def test_importe_es_texto_con_exactamente_2_decimales_y_moneda_iso(cliente: TestClient) -> None:
    for producto in cliente.get("/api/v2/productos").json():
        assert set(producto) == {"id", "nombre", "precio"}
        assert set(producto["precio"]) == {"importe", "moneda"}
        assert re.fullmatch(r"\d+\.\d{2}", producto["precio"]["importe"])
        assert re.fullmatch(r"[A-Z]{3}", producto["precio"]["moneda"])
        assert producto["precio"]["moneda"] == "EUR"


def test_importe_con_ceros_finales_se_conserva(cliente: TestClient) -> None:
    molinillo = cliente.get("/api/v2/productos/molinillo-manual").json()

    assert molinillo["precio"]["importe"] == "32.00"


def test_v2_coincide_con_v1_salvo_la_forma_del_precio(cliente: TestClient) -> None:
    v1 = cliente.get("/api/v1/productos").json()
    v2 = cliente.get("/api/v2/productos").json()

    assert [(p["id"], p["nombre"], p["precio"]) for p in v1] == [
        (p["id"], p["nombre"], p["precio"]["importe"]) for p in v2
    ]


def test_v2_es_publica_y_no_se_cachea(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v2/productos")

    assert "authorization" not in cliente.headers
    assert respuesta.status_code == 200
    assert respuesta.headers["cache-control"] == "no-store"


# --- Historia 2: búsqueda y errores iguales a v1 ---


@pytest.mark.parametrize("q", ["cafe", "CAFÉ", "zzz", "", "   ", "a" * 200, " cafe "])
def test_busqueda_v2_devuelve_lo_mismo_que_v1(cliente: TestClient, q: str) -> None:
    v1 = cliente.get("/api/v1/productos", params={"q": q})
    v2 = cliente.get("/api/v2/productos", params={"q": q})

    assert v2.status_code == v1.status_code == 200
    assert [p["id"] for p in v2.json()] == [p["id"] for p in v1.json()]
    assert v2.json() == [_v2(p) for p in v1.json()]


def test_q_demasiado_largo_da_el_mismo_422_que_v1(cliente: TestClient) -> None:
    v1 = cliente.get("/api/v1/productos", params={"q": "a" * 201})
    v2 = cliente.get("/api/v2/productos", params={"q": "a" * 201})

    assert v2.status_code == v1.status_code == 422
    assert v2.json() == v1.json() == {"detail": "Parámetro q no válido"}


@pytest.mark.parametrize("id_", ["no-existe", "ana@example.com", "%20", "A" * 300])
def test_id_inexistente_da_el_mismo_404_que_v1(cliente: TestClient, id_: str) -> None:
    v1 = cliente.get(f"/api/v1/productos/{id_}")
    v2 = cliente.get(f"/api/v2/productos/{id_}")

    assert v2.status_code == v1.status_code == 404
    assert v2.json() == v1.json()


def test_busqueda_v2_no_registra_el_texto_de_q(
    cliente: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("INFO", logger="app"):
        cliente.get("/api/v2/productos", params={"q": "textosecreto"})

    # Solo los logs de la aplicación: el cliente de pruebas registra su propia URL.
    registros = [r.getMessage() for r in caplog.records if r.name.startswith("app")]
    assert registros
    assert not any("textosecreto" in r for r in registros)
    assert any('"longitud_q": 12' in r for r in registros)


# --- Historia 4: métricas separadas por versión ---


def test_las_metricas_separan_v2_de_v1(cliente: TestClient) -> None:
    def valor(ruta: str) -> float:
        etiquetas = {"metodo": "GET", "ruta": ruta, "estado": "200"}
        return REGISTRY.get_sample_value("app_consultas_total", etiquetas) or 0.0

    antes_v1, antes_v2 = valor("/api/v1/productos"), valor("/api/v2/productos")
    cliente.get("/api/v2/productos")

    assert valor("/api/v2/productos") == antes_v2 + 1
    assert valor("/api/v1/productos") == antes_v1


def test_las_metricas_de_detalle_v2_no_llevan_el_id(cliente: TestClient) -> None:
    antes = (
        REGISTRY.get_sample_value(
            "app_consultas_total",
            {"metodo": "GET", "ruta": "/api/v2/productos/{id}", "estado": "404"},
        )
        or 0.0
    )
    cliente.get("/api/v2/productos/ana@example.com")

    despues = REGISTRY.get_sample_value(
        "app_consultas_total",
        {"metodo": "GET", "ruta": "/api/v2/productos/{id}", "estado": "404"},
    )
    assert despues == antes + 1


def test_v2_devuelve_la_moneda_del_catalogo(tmp_path: Path) -> None:
    ruta = tmp_path / "catalogo.json"
    productos = [{"id": f"p{n}", "nombre": f"Producto {n}", "precio": "1.00"} for n in range(5)]
    ruta.write_text(json.dumps({"moneda": "USD", "productos": productos}), encoding="utf-8")
    cliente = TestClient(create_app(ruta))

    listado = cliente.get("/api/v2/productos").json()
    detalle = cliente.get("/api/v2/productos/p0").json()

    assert {p["precio"]["moneda"] for p in listado} == {"USD"}
    assert detalle["precio"] == {"importe": "1.00", "moneda": "USD"}
