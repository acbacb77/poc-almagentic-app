import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.catalogo import RUTA_CATALOGO, Catalogo, cargar_catalogo, normalizar


def _productos(cantidad: int = 5) -> list[dict[str, Any]]:
    return [
        {"id": f"producto-{n}", "nombre": f"Producto {n}", "precio": "1.00"}
        for n in range(cantidad)
    ]


def _con_primer_producto(**cambios: Any) -> dict[str, Any]:
    productos = _productos()
    productos[0] = {**productos[0], **cambios}
    return {"productos": productos}


def test_el_catalogo_del_repositorio_es_valido() -> None:
    catalogo = cargar_catalogo(RUTA_CATALOGO)

    assert 5 <= len(catalogo.productos) <= 10


def test_cargar_catalogo_conserva_el_orden_del_fichero(tmp_path: Path) -> None:
    ruta = tmp_path / "catalogo.json"
    ruta.write_text(json.dumps({"productos": _productos(7)}), encoding="utf-8")

    catalogo = cargar_catalogo(ruta)

    assert [p.id for p in catalogo.productos] == [f"producto-{n}" for n in range(7)]


@pytest.mark.parametrize("cantidad", [5, 10])
def test_acepta_entre_5_y_10_productos(cantidad: int) -> None:
    catalogo = Catalogo.model_validate({"productos": _productos(cantidad)})

    assert len(catalogo.productos) == cantidad


@pytest.mark.parametrize("cantidad", [0, 4, 11])
def test_rechaza_menos_de_5_o_mas_de_10_productos(cantidad: int) -> None:
    with pytest.raises(ValidationError):
        Catalogo.model_validate({"productos": _productos(cantidad)})


def test_rechaza_identificadores_repetidos() -> None:
    with pytest.raises(ValidationError):
        Catalogo.model_validate(_con_primer_producto(id="producto-1"))


@pytest.mark.parametrize(
    "cambios",
    [
        {"id": ""},
        {"id": "   "},
        {"nombre": ""},
        {"nombre": "   "},
        {"precio": "-1.00"},
        {"precio": "1.999"},
        {"precio": "1.5"},
        {"precio": "1"},
        {"precio": 1.5},
        {"precio": "gratis"},
        {"moneda": "EUR"},
    ],
)
def test_rechaza_productos_mal_formados(cambios: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        Catalogo.model_validate(_con_primer_producto(**cambios))


@pytest.mark.parametrize("campo", ["id", "nombre", "precio"])
def test_rechaza_productos_sin_un_campo(campo: str) -> None:
    datos = _con_primer_producto()
    del datos["productos"][0][campo]

    with pytest.raises(ValidationError):
        Catalogo.model_validate(datos)


def test_cargar_catalogo_rechaza_un_fichero_mal_formado(tmp_path: Path) -> None:
    ruta = tmp_path / "catalogo.json"
    ruta.write_text(json.dumps(_con_primer_producto(precio="-1.00")), encoding="utf-8")

    with pytest.raises(ValidationError):
        cargar_catalogo(ruta)


# --- Búsqueda por nombre (spec 002) ---


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Cerámica", "ceramica"),
        ("CERÁMICA", "ceramica"),
        ("Año", "ano"),
        ("cafe\u0301", "cafe"),  # forma descompuesta
    ],
)
def test_normalizar_ignora_mayusculas_y_acentos(texto: str, esperado: str) -> None:
    assert normalizar(texto) == esperado


def test_buscar_por_nombre_filtra_por_fragmento_y_conserva_el_orden() -> None:
    catalogo = cargar_catalogo(RUTA_CATALOGO)

    ids = [p.id for p in catalogo.buscar_por_nombre("taza")]

    assert ids == ["taza-ceramica", "cafetera-italiana-6-tazas"]


@pytest.mark.parametrize("texto", ["%", "_", "*", ".*", "' OR 1=1 --"])
def test_buscar_por_nombre_trata_los_comodines_como_texto(texto: str) -> None:
    assert cargar_catalogo(RUTA_CATALOGO).buscar_por_nombre(texto) == []
