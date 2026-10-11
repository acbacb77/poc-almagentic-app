import json
import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import create_app
from app.observabilidad import SinQueryString

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


# --- Búsqueda por nombre (spec 002, FR-011) ---


def _busquedas(resultado: str) -> float:
    return REGISTRY.get_sample_value("app_busquedas_total", {"resultado": resultado}) or 0.0


def test_la_busqueda_registra_longitud_y_resultados_sin_el_texto(
    cliente: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="app.consultas"):
        cliente.get("/api/v1/productos", params={"q": "  taza  "})

    eventos = [log for log in _logs(caplog) if log["evento"] == "busqueda"]
    assert eventos == [{"evento": "busqueda", "longitud_q": 4, "resultados": 2}]
    assert "taza" not in caplog.text.lower()


def test_la_busqueda_incrementa_su_metrica_segun_haya_resultados(cliente: TestClient) -> None:
    con, sin = _busquedas("con_resultados"), _busquedas("sin_resultados")

    cliente.get("/api/v1/productos", params={"q": "taza"})
    cliente.get("/api/v1/productos", params={"q": "inexistente"})

    assert _busquedas("con_resultados") == con + 1
    assert _busquedas("sin_resultados") == sin + 1


def test_sin_q_o_con_q_vacio_no_hay_evento_de_busqueda(
    cliente: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    antes = _busquedas("con_resultados") + _busquedas("sin_resultados")

    with caplog.at_level(logging.INFO, logger="app.consultas"):
        cliente.get("/api/v1/productos")
        cliente.get("/api/v1/productos", params={"q": "  "})

    assert [log for log in _logs(caplog) if log["evento"] == "busqueda"] == []
    assert _busquedas("con_resultados") + _busquedas("sin_resultados") == antes


def test_el_log_de_acceso_de_uvicorn_no_incluye_la_query_string(
    caplog: pytest.LogCaptureFixture,
) -> None:
    create_app()
    acceso = logging.getLogger("uvicorn.access")
    with caplog.at_level(logging.INFO, logger="uvicorn.access"):
        acceso.info(
            '%s - "%s %s HTTP/%s" %d',
            "127.0.0.1:1234",
            "GET",
            "/api/v1/productos?q=secreto",
            "1.1",
            200,
        )
        acceso.info('%s - "%s %s HTTP/%s" %d', "127.0.0.1:1234", "GET", "/health", "1.1", 200)

    mensajes = [r.getMessage() for r in caplog.records if r.name == "uvicorn.access"]
    assert 'GET /api/v1/productos HTTP/1.1" 200' in mensajes[0]
    assert "secreto" not in mensajes[0] and "?" not in mensajes[0]
    assert 'GET /health HTTP/1.1" 200' in mensajes[1]


def test_configurar_logs_no_duplica_el_filtro_de_acceso() -> None:
    create_app()
    create_app()
    filtros = logging.getLogger("uvicorn.access").filters
    assert sum(isinstance(f, SinQueryString) for f in filtros) == 1
