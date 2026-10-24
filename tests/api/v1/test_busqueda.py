"""Spec 002: búsqueda de productos por nombre con el parámetro q."""

import json

import pytest
from fastapi.testclient import TestClient

from app.catalogo import RUTA_CATALOGO
from app.main import create_app

RUTA = "/api/v1/productos"
CATALOGO = json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))["productos"]
CON_TAZA = [p for p in CATALOGO if p["id"] in ("taza-ceramica", "cafetera-italiana-6-tazas")]
TAZA_CERAMICA = [p for p in CATALOGO if p["id"] == "taza-ceramica"]
MOLINILLO = [p for p in CATALOGO if p["id"] == "molinillo-manual"]


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app())


def _buscar(cliente: TestClient, q: str) -> list[dict[str, str]]:
    respuesta = cliente.get(RUTA, params={"q": q})
    assert respuesta.status_code == 200
    resultado: list[dict[str, str]] = respuesta.json()
    return resultado


# --- US1: filtrar por nombre ---


def test_q_devuelve_solo_los_productos_cuyo_nombre_contiene_el_texto(
    cliente: TestClient,
) -> None:
    assert _buscar(cliente, "taza") == CON_TAZA


def test_q_coincide_en_cualquier_posicion_del_nombre(cliente: TestClient) -> None:
    assert _buscar(cliente, "cerámica") == TAZA_CERAMICA  # final
    assert _buscar(cliente, "de ceram") == TAZA_CERAMICA  # medio, con espacio interior
    assert [p["id"] for p in _buscar(cliente, "mol")] == ["cafe-molido-250g", "molinillo-manual"]


def test_los_resultados_tienen_la_forma_y_el_orden_del_listado(cliente: TestClient) -> None:
    resultado = _buscar(cliente, "a")

    assert resultado == [p for p in CATALOGO if "a" in p["nombre"].lower()]
    assert all(set(p) == {"id", "nombre", "precio"} for p in resultado)


# --- US2: sin mayúsculas ni acentos ---


@pytest.mark.parametrize("q", ["ceramica", "CERÁMICA", "cerámica", "CeRaMiCa"])
def test_q_ignora_mayusculas_y_acentos(cliente: TestClient, q: str) -> None:
    assert _buscar(cliente, q) == TAZA_CERAMICA


def test_q_sin_acentos_encuentra_nombres_con_acentos_y_al_reves(cliente: TestClient) -> None:
    assert [p["id"] for p in _buscar(cliente, "te verde")] == ["te-verde-20-bolsitas"]
    assert [p["id"] for p in _buscar(cliente, "café")] == [
        "cafe-molido-250g",
        "cafetera-italiana-6-tazas",
    ]


def test_q_en_forma_unicode_descompuesta_tambien_coincide(cliente: TestClient) -> None:
    assert _buscar(cliente, "cerámica") == TAZA_CERAMICA


# --- US3: sin q y sin resultados ---


def test_sin_q_el_listado_es_el_catalogo_completo(cliente: TestClient) -> None:
    respuesta = cliente.get(RUTA)

    assert respuesta.status_code == 200
    assert respuesta.json() == CATALOGO


def test_sin_coincidencias_devuelve_200_y_lista_vacia(cliente: TestClient) -> None:
    respuesta = cliente.get(RUTA, params={"q": "inexistente"})

    assert respuesta.status_code == 200
    assert respuesta.json() == []


# --- Casos límite ---


@pytest.mark.parametrize("q", ["", "   ", "\t"])
def test_q_vacio_o_con_espacios_equivale_a_no_enviarlo(cliente: TestClient, q: str) -> None:
    assert _buscar(cliente, q) == CATALOGO


def test_q_con_mas_de_200_espacios_devuelve_el_catalogo_completo(cliente: TestClient) -> None:
    assert _buscar(cliente, " " * 250) == CATALOGO


def test_los_espacios_alrededor_de_q_se_ignoran(cliente: TestClient) -> None:
    assert _buscar(cliente, "  taza  ") == CON_TAZA


@pytest.mark.parametrize("q", ["%", "_", "*", ".*", "[a-z]", "'", '"', "\\", "' OR 1=1 --"])
def test_los_caracteres_especiales_son_texto_literal(cliente: TestClient, q: str) -> None:
    assert _buscar(cliente, q) == []


def test_con_q_repetido_no_hay_error_y_se_usa_un_solo_valor(cliente: TestClient) -> None:
    respuesta = cliente.get(f"{RUTA}?q=taza&q=molinillo")

    assert respuesta.status_code == 200
    assert respuesta.json() in (CON_TAZA, MOLINILLO)


def test_q_de_100_caracteres_o_menos_sigue_igual(cliente: TestClient) -> None:
    assert _buscar(cliente, "a" * 100) == []
    assert _buscar(cliente, f"  {'a' * 100}  ") == []


# --- Spec 003: límite de 200 caracteres ---


@pytest.mark.parametrize("longitud", [101, 120, 200])
def test_q_de_101_a_200_caracteres_es_valido(cliente: TestClient, longitud: int) -> None:
    assert _buscar(cliente, "a" * longitud) == []


def test_q_de_200_caracteres_cuenta_tras_quitar_espacios_de_los_extremos(
    cliente: TestClient,
) -> None:
    assert _buscar(cliente, f"  {'a' * 200}  ") == []
    assert _buscar(cliente, f" {'a' * 199} ") == []


def test_q_de_mas_de_200_caracteres_se_rechaza_con_un_422_generico(
    cliente: TestClient,
) -> None:
    respuesta = cliente.get(RUTA, params={"q": "secreto-" + "a" * 193})

    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": "Parámetro q no válido"}
    assert "secreto" not in respuesta.text


def test_q_de_201_caracteres_con_espacios_en_los_extremos_se_rechaza(
    cliente: TestClient,
) -> None:
    assert cliente.get(RUTA, params={"q": f" {'a' * 201} "}).status_code == 422


def test_q_se_cuenta_en_caracteres_no_en_bytes(cliente: TestClient) -> None:
    assert _buscar(cliente, "ñ" * 200) == []
    assert cliente.get(RUTA, params={"q": "ñ" * 201}).status_code == 422


def test_la_consulta_por_identificador_no_cambia(cliente: TestClient) -> None:
    respuesta = cliente.get(f"{RUTA}/taza-ceramica", params={"q": "otra-cosa"})

    assert respuesta.status_code == 200
    assert respuesta.json() == TAZA_CERAMICA[0]


def test_las_respuestas_de_busqueda_no_se_cachean(cliente: TestClient) -> None:
    assert cliente.get(RUTA, params={"q": "taza"}).headers["cache-control"] == "no-store"
    assert cliente.get(RUTA, params={"q": "x" * 201}).headers["cache-control"] == "no-store"
