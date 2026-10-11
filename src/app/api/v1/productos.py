from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.catalogo import Catalogo, Producto

router = APIRouter(prefix="/productos", tags=["productos"])


def _catalogo(request: Request) -> Catalogo:
    catalogo: Catalogo = request.app.state.catalogo
    return catalogo


CatalogoDep = Annotated[Catalogo, Depends(_catalogo)]


@router.get("")
def listar_productos(catalogo: CatalogoDep) -> list[Producto]:
    return catalogo.productos


# `id` es un texto opaco sin restricciones: cualquier valor que no coincida
# con un producto recibe 404, nunca 422.
@router.get("/{id}", responses={404: {"description": "Producto no encontrado"}})
def consultar_producto(id: str, catalogo: CatalogoDep) -> Producto:
    producto = catalogo.buscar(id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto
