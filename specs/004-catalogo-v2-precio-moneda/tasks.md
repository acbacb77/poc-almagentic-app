# Tareas: Catálogo v2 con importe y moneda, y v1 obsoleta

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

- [x] T001 Añadir `moneda` (ISO 4217, `EUR`) a `Catalogo` en `src/app/catalogo.py` (FR-005)
- [x] T002 `ProductoV1` explícito en `src/app/api/v1/productos.py` para que v1 no cambie (FR-013)
- [x] T003 [US1] Router v2 con `ProductoV2`/`Precio` en `src/app/api/v2/productos.py` (FR-001..FR-004, FR-008)
- [x] T004 [US2] Búsqueda `q` y errores 404/422 iguales a v1 en v2 (FR-006, FR-007, FR-017, FR-018)
- [x] T005 [US3] Middleware `aviso_obsolescencia_v1` en `src/app/main.py` y montaje del router v2 (FR-010..FR-012, FR-015)
- [x] T006 [US1][US2] Tests en `tests/api/v2/test_productos_v2.py`
- [x] T007 [US3] Tests en `tests/api/v1/test_obsolescencia.py`
- [x] T008 [US4] Tests de métricas separadas por versión (FR-016) en `tests/api/v2/test_productos_v2.py`
- [x] T009 Ejecutar pytest, ruff y mypy
