# Plan de implementación: spec 006 (log de acceso de v1 y /api/v1 sin barra)

**Spec**: [spec.md](spec.md) · **Issue**: #44 · **Constitución**: sin conflictos (I seguridad, VI simplicidad).

## Decisiones

- **Log**: nuevo filtro `SinRutaV1` en `src/app/observabilidad.py`, registrado en `uvicorn.access` junto a `SinQueryString` (idempotente). Decodifica la ruta y, si es `/api/v1` o empieza por `/api/v1/`, la sustituye por `/api/v1/[retirada]`. Cualquier otra ruta queda intacta (`/api/v10`, v2, `/health`).
- **Sin barra**: se añade a la ruta comodín de v1 una segunda ruta con path `""` (`/api/v1`) en `src/app/api/v1/productos.py`. `redirect_slashes` no se toca. El `Link` de `/api/v1` es `/api/v2`.
- **Métricas y logs propios**: sin cambios; solo tests.
- Sin dependencias nuevas, sin cambios en Dockerfile ni en contratos publicados.

## Tests

`tests/api/v1/test_retirada_log_barra.py`, uno o más por escenario de aceptación de las US1–US4.
