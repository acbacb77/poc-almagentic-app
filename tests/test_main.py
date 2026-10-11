from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import create_app


def test_la_aplicacion_no_arranca_con_un_catalogo_mal_formado(tmp_path: Path) -> None:
    ruta = tmp_path / "catalogo.json"
    ruta.write_text('{"productos": []}', encoding="utf-8")

    with pytest.raises(ValidationError):
        create_app(ruta)


def test_health_responde_ok_sin_credenciales() -> None:
    cliente = TestClient(create_app())

    respuesta = cliente.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}
