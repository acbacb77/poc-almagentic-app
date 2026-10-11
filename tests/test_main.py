from fastapi.testclient import TestClient

from app.main import create_app


def test_health_responde_ok_sin_credenciales() -> None:
    cliente = TestClient(create_app())

    respuesta = cliente.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}
