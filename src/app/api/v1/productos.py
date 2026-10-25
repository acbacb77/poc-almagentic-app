from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.catalogo import Catalogo, Producto
from app.observabilidad import registrar_busqueda

router = APIRouter(prefix="/api/v1/productos", tags=["productos"])

LONGITUD_MAXIMA_Q = 200


class ProductoV1(BaseModel):
    """Forma publicada de v1: no incluye la moneda (spec 004, FR-013)."""

    id: str
    nombre: str
    precio: Decimal = Field(
        description="Importe en euros, IVA incluido, con exactamente 2 decimales."
    )


def a_v1(producto: Producto) -> ProductoV1:
    return ProductoV1(id=producto.id, nombre=producto.nombre, precio=producto.precio)


def _catalogo(request: Request) -> Catalogo:
    catalogo: Catalogo = request.app.state.catalogo
    return catalogo


CatalogoDep = Annotated[Catalogo, Depends(_catalogo)]


# `q` se valida a mano: la longitud cuenta tras quitar espacios y el 422 por
# defecto de FastAPI devolvería el texto recibido (FR-009, FR-012).
@router.get(
    "",
    responses={422: {"description": "Parámetro q no válido"}},
)
def listar_productos(catalogo: CatalogoDep, q: str | None = None) -> list[ProductoV1]:
    texto = (q or "").strip()
    if not texto:
        return [a_v1(p) for p in catalogo.productos]
    if len(texto) > LONGITUD_MAXIMA_Q:
        raise HTTPException(status_code=422, detail="Parámetro q no válido")
    encontrados = catalogo.buscar_por_nombre(texto)
    registrar_busqueda(len(texto), len(encontrados))
    return [a_v1(p) for p in encontrados]


# `id` es un texto opaco sin restricciones: cualquier valor que no coincida
# con un producto recibe 404, nunca 422.
@router.get("/{id}", responses={404: {"description": "Producto no encontrado"}})
def consultar_producto(id: str, catalogo: CatalogoDep) -> ProductoV1:
    producto = catalogo.buscar(id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return a_v1(producto)
