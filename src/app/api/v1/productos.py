from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.catalogo import Catalogo, Producto
from app.observabilidad import registrar_busqueda

router = APIRouter(prefix="/api/v1/productos", tags=["productos"])

LONGITUD_MAXIMA_Q = 200


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
def listar_productos(catalogo: CatalogoDep, q: str | None = None) -> list[Producto]:
    texto = (q or "").strip()
    if not texto:
        return catalogo.productos
    if len(texto) > LONGITUD_MAXIMA_Q:
        raise HTTPException(status_code=422, detail="Parámetro q no válido")
    encontrados = catalogo.buscar_por_nombre(texto)
    registrar_busqueda(len(texto), len(encontrados))
    return encontrados


# `id` es un texto opaco sin restricciones: cualquier valor que no coincida
# con un producto recibe 404, nunca 422.
@router.get("/{id}", responses={404: {"description": "Producto no encontrado"}})
def consultar_producto(id: str, catalogo: CatalogoDep) -> Producto:
    producto = catalogo.buscar(id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto
