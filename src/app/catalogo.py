from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RUTA_CATALOGO = Path(__file__).parent / "catalogo.json"


class Producto(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    precio: Decimal = Field(ge=0, description="Euros, IVA incluido, con 2 decimales")

    @field_validator("precio")
    @classmethod
    def _exactamente_dos_decimales(cls, precio: Decimal) -> Decimal:
        if precio.as_tuple().exponent != -2:
            raise ValueError("el precio debe tener exactamente 2 decimales")
        return precio


class Catalogo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    productos: list[Producto] = Field(min_length=5, max_length=10)

    @model_validator(mode="after")
    def _identificadores_unicos(self) -> "Catalogo":
        ids = [producto.id for producto in self.productos]
        if len(ids) != len(set(ids)):
            raise ValueError("hay identificadores de producto repetidos")
        return self

    def buscar(self, id_producto: str) -> Producto | None:
        return next((p for p in self.productos if p.id == id_producto), None)


def cargar_catalogo(ruta: Path = RUTA_CATALOGO) -> Catalogo:
    return Catalogo.model_validate_json(ruta.read_text(encoding="utf-8"))
