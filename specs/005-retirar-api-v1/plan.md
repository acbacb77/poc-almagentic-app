# Plan: Retirar la API v1 del catálogo

**Spec**: [spec.md](spec.md)

## Decisiones

- **Una ruta comodín** `/api/v1/{ruta:resto}` (todos los métodos, `include_in_schema=False`) sustituye a los endpoints de v1. Así no hay 404/405/422 en v1 (FR-001, FR-003), no se valida nada (FR-004) y la plantilla de ruta en métricas y logs es siempre la misma (FR-011..FR-013). El convertidor `resto` es como `path` pero casa saltos de línea, para que ninguna ruta escape al 410.
- **Cabeceras** `Deprecation`, `Sunset` y `Link` se ponen en el propio handler (se elimina el middleware `aviso_obsolescencia_v1`). `Link` = ruta recibida con `v1`→`v2` + `q` si viene, todo codificado con `quote` (FR-006, FR-007).
- **Cuerpo** `{"detail": "Este recurso ha sido retirado"}` fijo, sin eco (FR-002); HEAD sin cuerpo.
- **v2** deja de importar de v1: `LONGITUD_MAXIMA_Q` y la dependencia del catálogo se mueven a `api/v2/productos.py`, sin cambio de comportamiento (FR-009).
- **Specs** 001–003: línea `Retirada` en la cabecera (FR-015).
- Sin dependencias nuevas, sin cambios en `Dockerfile`.

## Tests

`tests/api/v1/test_retirada.py` sustituye a los tests de v1 (FR-014). Los tests de v2 y `/health` no se tocan.
