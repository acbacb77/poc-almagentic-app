import json
import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import create_app

RUTA_LISTADO = "/api/v1/productos"
RUTA_PRODUCTO = "/api/v1/productos/{id}"


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app())


def _consultas(ruta: str, estado: str) -> float:
    etiquetas = {"metodo": "GET", "ruta": ruta, "estado": estado}
    return REGISTRY.get_sample_value("app_consultas_total", etiquetas) or 0.0


def _logs(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [json.loads(r.getMessage()) for r in caplog.records if r.name == "app.consultas"]


@pytest.mark.parametrize(
    ("url", "ruta", "estado"),
    [
        ("/api/v1/productos", RUTA_LISTADO, 200),
        ("/api/v1/productos/cafe-molido-250g", RUTA_PRODUCTO, 200),
        ("/api/v1/productos/no-existe", RUTA_PRODUCTO, 404),
    ],
)
def test_cada_consulta_deja_un_log_estructurado(
    cliente: TestClient, caplog: pytest.LogCaptureFixture, url: str, ruta: str, estado: int
) -> None:
    with caplog.at_level(logging.INFO, logger="app.consultas"):
        cliente.get(url)

    [log] = _logs(caplog)
    assert set(log) == {"evento", "metodo", "ruta", "estado", "duracion_ms"}
    assert log["evento"] == "consulta"
    assert log["metodo"] == "GET"
    assert log["ruta"] == ruta
    assert log["estado"] == estado
    assert log["duracion_ms"] >= 0


def test_el_log_no_contiene_datos_del_cliente(
    cliente: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="app.consultas"):
        cliente.get(
            "/api/v1/productos/ana.garcia@example.com?token=secreto",
            headers={"User-Agent": "navegador-de-ana", "Authorization": "Bearer secreto"},
        )

    assert len(_logs(caplog)) == 1
    for texto in ("ana", "example.com", "secreto", "testclient"):
        assert texto not in caplog.text


@pytest.mark.parametrize(
    ("url", "ruta", "estado"),
    [
        ("/api/v1/productos", RUTA_LISTADO, "200"),
        ("/api/v1/productos/cafe-molido-250g", RUTA_PRODUCTO, "200"),
        ("/api/v1/productos/no-existe", RUTA_PRODUCTO, "404"),
    ],
)
def test_cada_consulta_incrementa_su_metrica(
    cliente: TestClient, url: str, ruta: str, estado: str
) -> None:
    antes = _consultas(ruta, estado)
    duraciones_antes = (
        REGISTRY.get_sample_value(
            "app_consulta_duracion_segundos_count", {"metodo": "GET", "ruta": ruta}
        )
        or 0.0
    )

    cliente.get(url)

    assert _consultas(ruta, estado) == antes + 1
    assert (
        REGISTRY.get_sample_value(
            "app_consulta_duracion_segundos_count", {"metodo": "GET", "ruta": ruta}
        )
        == duraciones_antes + 1
    )


def test_metrics_expone_las_consultas_sin_identificadores(cliente: TestClient) -> None:
    cliente.get("/api/v1/productos")
    cliente.get("/api/v1/productos/identificador-arbitrario")

    respuesta = cliente.get("/metrics")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/plain")
    assert 'app_consultas_total{estado="200",metodo="GET",ruta="/api/v1/productos"}' in (
        respuesta.text
    )
    assert 'ruta="/api/v1/productos/{id}"' in respuesta.text
    assert "identificador-arbitrario" not in respuesta.text


def test_health_y_metrics_no_generan_logs_de_consulta(
    cliente: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="app.consultas"):
        cliente.get("/health")
        cliente.get("/metrics")

    assert _logs(caplog) == []
