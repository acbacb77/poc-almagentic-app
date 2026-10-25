# Plan de implementación: Catálogo v2 con importe y moneda, y v1 obsoleta

**Spec**: [spec.md](spec.md) · **Issue**: #36 · **Rama**: `feat/36-catalogo-v2-precio-moneda`

## Resumen

Se añade un router `/api/v2/productos` con la misma lógica de búsqueda y errores que v1 y el precio como `{importe, moneda}`. Un middleware añade `Deprecation`, `Sunset` y `Link` a las respuestas de v1. Las métricas ya etiquetan por plantilla de ruta, así que v2 se separa de v1 sin cambios.

## Contexto técnico

Python 3.12, FastAPI, Pydantic v2, pytest, ruff, mypy. Sin dependencias nuevas.

## Comprobación de la constitución

- I Seguridad: `q` e `id` se codifican con `urllib.parse.quote(safe="")` en `Link`; errores genéricos; `q` nunca se registra.
- II/III: cada criterio de aceptación tiene test.
- VI Simplicidad: v2 reutiliza `CatalogoDep` y `LONGITUD_MAXIMA_Q` de v1.
- Anexo: v1 no cambia de forma incompatible; v2 expone métricas y logs sin datos personales.

## Decisiones

1. **Modelo v1 propio** (`ProductoV1`): v1 serializa explícitamente `id`, `nombre`, `precio`, de modo que cualquier dato nuevo del catálogo no altere v1.
2. **Moneda**: atributo `moneda` del `Catalogo` (ISO 4217, valor `EUR`), leído del dato y no fijado en el endpoint. Los productos no la llevan porque la spec 001 y su test prohíben campos desconocidos en `Producto`; `catalogo.json` no cambia.
3. **Importe**: `format(Decimal, "f")`; el catálogo garantiza ya 2 decimales (spec 001), sin redondeo.
4. **Cabeceras de v1**: middleware `aviso_obsolescencia_v1` en `main.py`, basado en la plantilla de ruta casada (`/api/v1/productos` y `/api/v1/productos/{id}`), de modo que cubre 404 y 422 y no afecta a rutas desconocidas, v2 ni `/health`. Valores fijos (FR-012).
5. **Observabilidad**: sin cambios; `app_consultas_total` ya lleva la etiqueta `ruta` con la plantilla (`/api/v2/...`).

## Estructura

```
src/app/api/v2/productos.py   # router v2, ProductoV2, Precio
src/app/api/v1/productos.py   # ProductoV1 (sin moneda)
src/app/catalogo.py           # Catalogo.moneda
src/app/main.py               # router v2 y middleware de obsolescencia
tests/api/v2/test_productos_v2.py
tests/api/v1/test_obsolescencia.py
```
