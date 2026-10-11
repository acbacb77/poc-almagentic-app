"""FR-009: la API no cachea respuestas y lo declara a la tienda y a los proxies."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app())


@pytest.mark.parametrize(
    ("ruta", "estado"),
    [
        ("/api/v1/productos", 200),
        ("/api/v1/productos/taza-ceramica", 200),
        ("/api/v1/productos/no-existe", 404),
    ],
)
def test_las_respuestas_del_catalogo_no_se_cachean(cliente: TestClient, ruta: str, estado: int) -> None:
    respuesta = cliente.get(ruta)

    assert respuesta.status_code == estado
    assert respuesta.headers.get("cache-control") == "no-store"
