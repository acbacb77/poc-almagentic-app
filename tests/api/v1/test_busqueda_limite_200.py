"""Spec 003: el log de búsqueda registra solo la longitud de q, también con las longitudes nuevas."""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

RUTA = "/api/v1/productos"


@pytest.mark.parametrize("longitud", [150, 200])
def test_el_log_de_busqueda_registra_la_longitud_y_nunca_el_texto(
    caplog: pytest.LogCaptureFixture, longitud: int
) -> None:
    cliente = TestClient(create_app())
    texto = "zq" * (longitud // 2)

    with caplog.at_level(logging.INFO, logger="app"):
        respuesta = cliente.get(RUTA, params={"q": texto})

    assert respuesta.status_code == 200
    eventos = [json.loads(r.getMessage()) for r in caplog.records if "busqueda" in r.getMessage()]
    assert eventos == [{"evento": "busqueda", "longitud_q": longitud, "resultados": 0}]
    assert "zq" not in caplog.text


def test_una_busqueda_rechazada_no_registra_el_texto(caplog: pytest.LogCaptureFixture) -> None:
    cliente = TestClient(create_app())

    with caplog.at_level(logging.INFO, logger="app"):
        respuesta = cliente.get(RUTA, params={"q": "zq" * 101})

    assert respuesta.status_code == 422
    assert "zq" not in caplog.text
