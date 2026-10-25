# Tareas: spec 006

- [X] T001 Filtro `SinRutaV1` y registro en `configurar_logs` (`src/app/observabilidad.py`) — FR-001–005
- [X] T002 Ruta `""` para `/api/v1` sin barra y `Link` a `/api/v2` (`src/app/api/v1/productos.py`) — FR-006–008, FR-010
- [X] T003 Tests de log de acceso (v1 con marcador; v2, `/health` y `/api/v10` sin cambios) — US1, US3
- [X] T004 Tests de 410 sin barra en los 7 métodos, cabeceras, sin `Location`, métricas y `redirect_slashes` de v2 — US2, US3
- [X] T005 Test de métricas y logs propios sin la ruta recibida — US4
- [X] T006 pytest, ruff y mypy en verde
