# Data Model: Catálogo de productos

## Producto

Artículo que la tienda web muestra. Es a la vez el modelo del fichero y el de la respuesta de la API (FR-003).

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | cadena | No vacío tras recortar espacios. Único en el catálogo y estable en el tiempo. |
| `nombre` | cadena | No vacío tras recortar espacios. |
| `precio` | decimal | Euros, IVA incluido. No negativo. Exactamente 2 decimales. En JSON es una cadena (`"12.50"`). |

No se admiten campos adicionales.

## Catálogo

Lista ordenada de productos que el equipo mantiene en `src/app/catalogo.json`.

| Campo | Tipo | Reglas |
|---|---|---|
| `productos` | lista de Producto | Entre 5 y 10 elementos. Sin identificadores repetidos. El orden del fichero es el orden del listado (FR-008). |

Formato del fichero:

```json
{
  "productos": [
    {"id": "cafe-molido-250g", "nombre": "Café molido 250 g", "precio": "4.95"}
  ]
}
```

## Ciclo de vida

El catálogo es inmutable mientras el proceso está en marcha. Solo cambia con un PR que modifica el fichero y un despliegue. No hay transiciones de estado.

## Trazabilidad con los requisitos

| Regla | Requisito |
|---|---|
| Campos exactos de Producto | FR-003 |
| Precio con 2 decimales | FR-004 |
| Entre 5 y 10 productos en un fichero del repositorio | FR-007 |
| Orden estable | FR-008 |
| Rechazo de catálogos mal formados | FR-010 |
