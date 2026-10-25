# Tareas: Retirar la API v1 del catálogo

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

- [x] T001 [US1][US2] Ruta comodín 410 con `Deprecation`, `Sunset` y `Link` en `src/app/api/v1/productos.py` (FR-001..FR-007)
- [x] T002 Quitar el middleware de obsolescencia y montar el router en `src/app/main.py` (FR-004)
- [x] T003 [US3] Mover `LONGITUD_MAXIMA_Q` y la dependencia del catálogo a `src/app/api/v2/productos.py` (FR-009)
- [x] T004 [US1][US2][US4][US5] Sustituir los tests de v1 por `tests/api/v1/test_retirada.py` (FR-014)
- [x] T005 [US5] Marcar v1 como retirada en las specs 001, 002 y 003 (FR-015)
- [x] T006 Ejecutar pytest, ruff y mypy
