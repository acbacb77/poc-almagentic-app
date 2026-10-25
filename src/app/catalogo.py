import unicodedata
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RUTA_CATALOGO = Path(__file__).parent / "catalogo.json"


def normalizar(texto: str) -> str:
    """Minúsculas y sin acentos, para comparar textos de búsqueda."""
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).casefold()


class Producto(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    precio: Decimal = Field(
        ge=0, description="Importe en euros, IVA incluido, con exactamente 2 decimales."
    )

    @field_validator("precio")
    @classmethod
    def _exactamente_dos_decimales(cls, precio: Decimal) -> Decimal:
        if precio.as_tuple().exponent != -2:
            raise ValueError("el precio debe tener exactamente 2 decimales")
        return precio


class Catalogo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # Moneda del catálogo (ISO 4217), común a todos sus productos. Es un dato, sin valor
    # por defecto.
    moneda: str = Field(pattern=r"^[A-Z]{3}$")
    productos: list[Producto] = Field(min_length=5, max_length=10)

    @model_validator(mode="after")
    def _identificadores_unicos(self) -> "Catalogo":
        ids = [producto.id for producto in self.productos]
        if len(ids) != len(set(ids)):
            raise ValueError("hay identificadores de producto repetidos")
        return self

    def buscar(self, id_producto: str) -> Producto | None:
        return next((p for p in self.productos if p.id == id_producto), None)

    def buscar_por_nombre(self, texto: str) -> list[Producto]:
        """Productos cuyo nombre contiene `texto` (literal), en el orden del catálogo."""
        buscado = normalizar(texto)
        return [p for p in self.productos if buscado in normalizar(p.nombre)]


def cargar_catalogo(ruta: Path = RUTA_CATALOGO) -> Catalogo:
    return Catalogo.model_validate_json(ruta.read_text(encoding="utf-8"))
