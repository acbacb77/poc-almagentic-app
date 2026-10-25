from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.v1.productos import LONGITUD_MAXIMA_Q, CatalogoDep
from app.catalogo import Producto
from app.observabilidad import registrar_busqueda

router = APIRouter(prefix="/api/v2/productos", tags=["productos"])


class Precio(BaseModel):
    importe: str
    moneda: str


class ProductoV2(BaseModel):
    id: str
    nombre: str
    precio: Precio


def a_v2(producto: Producto, moneda: str) -> ProductoV2:
    # El catálogo ya garantiza exactamente 2 decimales: el importe es ese valor, sin redondeo.
    precio = Precio(importe=format(producto.precio, "f"), moneda=moneda)
    return ProductoV2(id=producto.id, nombre=producto.nombre, precio=precio)


# Mismas reglas que v1 para `q` y para los errores (FR-006, FR-007).
@router.get("", responses={422: {"description": "Parámetro q no válido"}})
def listar_productos(catalogo: CatalogoDep, q: str | None = None) -> list[ProductoV2]:
    texto = (q or "").strip()
    if not texto:
        return [a_v2(p, catalogo.moneda) for p in catalogo.productos]
    if len(texto) > LONGITUD_MAXIMA_Q:
        raise HTTPException(status_code=422, detail="Parámetro q no válido")
    encontrados = catalogo.buscar_por_nombre(texto)
    registrar_busqueda(len(texto), len(encontrados))
    return [a_v2(p, catalogo.moneda) for p in encontrados]


@router.get("/{id}", responses={404: {"description": "Producto no encontrado"}})
def consultar_producto(id: str, catalogo: CatalogoDep) -> ProductoV2:
    producto = catalogo.buscar(id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return a_v2(producto, catalogo.moneda)
