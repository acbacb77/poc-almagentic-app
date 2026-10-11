# Tasks: Buscar productos del catálogo por nombre

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

## Phase 1: Base (US1, US2)

- [x] T001 [US2] Tests de `normalizar` y `Catalogo.buscar_por_nombre` en `tests/test_catalogo.py`
- [x] T002 [US1] [US2] Implementar `normalizar` y `buscar_por_nombre` en `src/app/catalogo.py`

## Phase 2: Endpoint (US1, US2, US3)

- [x] T003 [US1] [US2] [US3] Tests HTTP en `tests/api/v1/test_busqueda.py` (todos los escenarios y casos límite)
- [x] T004 [US1] [US2] [US3] Parámetro `q`, validación y 422 genérico en `src/app/api/v1/productos.py`

## Phase 3: Observabilidad (FR-011)

- [x] T005 Tests de log y métrica de búsqueda en `tests/test_observabilidad.py`
- [x] T006 Contador y log de búsqueda en `src/app/observabilidad.py`, usados desde el endpoint

## Phase 4: Cierre

- [x] T007 pytest, ruff y mypy en verde
