# Implementation Plan: Catálogo de productos

**Branch**: `feat/5-catalogo-productos` | **Date**: 2026-10-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-catalogo-productos/spec.md`

**Issue**: #5

## Summary

Dos consultas públicas de solo lectura, `GET /api/v1/productos` y `GET /api/v1/productos/{id}`, que sirven un catálogo fijo de 5 a 10 productos mantenido en un fichero JSON del repositorio. El catálogo se valida con Pydantic al arrancar la aplicación y en los tests, de modo que un catálogo mal formado nunca llega a servirse.

Por decisión del responsable en el PR #9, esta feature crea además el esqueleto de la aplicación: `pyproject.toml` con `uv`, `src/app/main.py` con `GET /health` y la estructura descrita en `AGENTS.md`.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI, Pydantic v2, uvicorn (arranque local), prometheus-client (métricas, FR-012)

**Storage**: fichero `src/app/catalogo.json` versionado en el repositorio; sin base de datos

**Testing**: pytest con `fastapi.testclient.TestClient` (requiere `httpx` como dependencia de desarrollo)

**Target Platform**: servidor Linux (contenedor); el despliegue vive en `poc-almagentic-gitops`

**Project Type**: web-service (API REST)

**Performance Goals**: menos de 1 segundo por consulta (SC-005); el catálogo está en memoria, así que se cumple con margen

**Constraints**: sin caché de respuestas (FR-009), sin autenticación (FR-006), rutas versionadas bajo `/api/v1` (FR-011), mensajes de error genéricos (constitución I)

**Scale/Scope**: 5 a 10 productos, 2 endpoints de negocio, más `/health` y `/metrics`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo se cumple | Estado |
|---|---|---|
| I. Seguridad por defecto | No hay secretos. La única entrada externa es `{id}`, que se usa solo como clave de búsqueda exacta en memoria. El catálogo se valida con un esquema Pydantic estricto. El 404 lleva un mensaje fijo y genérico. Dependencias de PyPI con versión fijada y licencias MIT, BSD o Apache-2.0. | PASA |
| II. Spec primero | Issue #5 aprobado y spec fusionada en el PR #9. El esqueleto se crea por decisión explícita del responsable en ese PR. | PASA |
| III. Tests como contrato | Cada escenario de aceptación y cada caso límite tiene al menos un test; los tests se escriben junto con el código en este mismo PR. | PASA |
| IV. Trazabilidad | Rama `feat/5-catalogo-productos`, commits con `Refs #5`, PR con `Closes #5` y enlace a la spec. | PASA |
| V. Control humano | El PR lo aprueba y fusiona un humano. No se tocan ficheros de gobierno. | PASA |
| VI. Simplicidad | Catálogo en un JSON cargado en memoria, sin capas de repositorio ni servicio. Una sola dependencia de ejecución más allá del stack (`prometheus-client`), justificada en [research.md](./research.md). | PASA |
| Anexo: compatibilidad | Rutas nuevas bajo `/api/v1`; no se modifica ninguna versión publicada. | PASA |
| Anexo: observabilidad | Cada consulta deja un log JSON y actualiza un contador y un histograma, etiquetados con la plantilla de la ruta, no con el valor de `{id}`. | PASA |

**Revisión tras el diseño (Phase 1)**: sin cambios; no hay violaciones que justificar.

## Project Structure

### Documentation (this feature)

```text
specs/001-catalogo-productos/
├── plan.md              # Este fichero
├── research.md          # Decisiones de diseño
├── data-model.md        # Producto y Catálogo
├── quickstart.md        # Guía de validación
├── contracts/
│   └── openapi.yaml     # Contrato de /api/v1/productos
└── tasks.md             # Lo genera /speckit-tasks
```

### Source Code (repository root)

```text
pyproject.toml                  # dependencias (uv), configuración de pytest, ruff y mypy
uv.lock
src/app/
├── __init__.py
├── main.py                     # create_app(): /health, /metrics, router v1, middleware de observabilidad
├── catalogo.py                 # modelos Producto y Catalogo, cargar_catalogo()
├── catalogo.json               # catálogo de ejemplo (FR-007)
├── observabilidad.py           # log JSON y métricas por consulta
└── api/
    ├── __init__.py
    └── v1/
        ├── __init__.py
        └── productos.py        # GET /productos y GET /productos/{id}

tests/
├── test_main.py                # /health
├── test_catalogo.py            # validación del catálogo (FR-010)
├── test_observabilidad.py      # FR-012
└── api/v1/test_productos.py    # historias de usuario 1, 2 y 3
```

**Structure Decision**: proyecto único con la estructura que fija `AGENTS.md` (`src/app/main.py`, `src/app/api/v1/`, `tests/` como espejo de `src/`). La aplicación no se empaqueta: `pytest` y `mypy` resuelven `app` desde `src/`, igual que `uvicorn --app-dir src`.

## Complexity Tracking

Sin violaciones de la constitución.
