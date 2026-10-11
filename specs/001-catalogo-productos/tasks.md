---

description: "Lista de tareas de la feature Catálogo de productos"
---

# Tasks: Catálogo de productos

**Input**: Design documents from `/specs/001-catalogo-productos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: obligatorios. La constitución (III) exige al menos un test por criterio de aceptación, escrito antes o junto con el código.

**Organization**: las tareas se agrupan por historia de usuario para poder implementar y probar cada una por separado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (ficheros distintos, sin dependencias)
- **[Story]**: historia de usuario a la que pertenece (US1, US2, US3)

## Path Conventions

Proyecto único: `src/app/` y `tests/` en la raíz del repositorio, según `AGENTS.md`.

---

## Phase 1: Setup (esqueleto de la aplicación)

**Purpose**: crear el proyecto, por decisión del responsable en el PR #9

- [ ] T001 Crear `pyproject.toml` con Python 3.12, `[tool.uv] package = false`, dependencias con versión fijada (`fastapi`, `uvicorn`, `prometheus-client`; dev: `pytest`, `httpx`, `ruff`, `mypy`) y la configuración de pytest (`pythonpath = ["src"]`), ruff y mypy (`strict`, `mypy_path = "src"`); generar `uv.lock` con `uv sync`
- [ ] T002 [P] Crear los paquetes vacíos `src/app/__init__.py`, `src/app/api/__init__.py` y `src/app/api/v1/__init__.py`
- [ ] T003 Escribir el test de `GET /health` (200, `{"status": "ok"}`, sin credenciales) en `tests/test_main.py`
- [ ] T004 Implementar `create_app()` y `app` con `GET /health` en `src/app/main.py`

---

## Phase 2: Foundational (catálogo validado)

**Purpose**: el modelo y la carga del catálogo, de los que dependen todas las historias

**⚠️ CRITICAL**: ninguna historia puede empezar antes de terminar esta fase

- [ ] T005 Escribir en `tests/test_catalogo.py` los tests de validación (FR-007, FR-010): el fichero real `src/app/catalogo.json` es válido y tiene entre 5 y 10 productos; se rechazan identificadores repetidos, `id` o `nombre` vacíos o solo con espacios, precio negativo, precio con más o con menos de 2 decimales, campos extra, menos de 5 y más de 10 productos
- [ ] T006 Implementar en `src/app/catalogo.py` los modelos `Producto` (`id`: "No vacío tras recortar espacios"; `nombre`: "No vacío tras recortar espacios"; `precio`: "No negativo. Exactamente 2 decimales"; "No se admiten campos adicionales") y `Catalogo` (`productos`: "Entre 5 y 10 elementos. Sin identificadores repetidos"), y la función `cargar_catalogo(ruta)` que lee y valida el JSON
- [ ] T007 [P] Crear el catálogo de ejemplo con entre 5 y 10 productos en `src/app/catalogo.json`, con el precio como cadena de 2 decimales
- [ ] T008 Cargar el catálogo en `create_app(ruta_catalogo)` y guardarlo en `app.state.catalogo` en `src/app/main.py`, de modo que un catálogo no válido impida arrancar; añadir el test correspondiente en `tests/test_main.py`

**Checkpoint**: el catálogo se valida al arrancar y en los tests

---

## Phase 3: User Story 1 - Consultar el catálogo completo (Priority: P1) 🎯 MVP

**Goal**: `GET /api/v1/productos` devuelve todos los productos con identificador, nombre y precio

**Independent Test**: consultar el listado sin credenciales y comprobar que contiene todos los productos del catálogo

### Tests for User Story 1

- [ ] T009 [US1] Escribir en `tests/api/v1/test_productos.py` los tests del listado: devuelve el catálogo completo con exactamente `id`, `nombre` y `precio` (escenario 1, FR-003); responde 200 sin credenciales (escenario 2, FR-006); cada precio es una cadena con exactamente 2 decimales (escenario 3, FR-004); dos consultas seguidas devuelven lo mismo y en el orden del fichero (FR-008)

### Implementation for User Story 1

- [ ] T010 [US1] Implementar `GET /productos` con `response_model=list[Producto]` en `src/app/api/v1/productos.py`
- [ ] T011 [US1] Montar el router con el prefijo `/api/v1` en `src/app/main.py`

**Checkpoint**: la tienda ya puede pintar el listado

---

## Phase 4: User Story 2 - Consultar un producto por su identificador (Priority: P2)

**Goal**: `GET /api/v1/productos/{id}` devuelve el producto o un 404 genérico

**Independent Test**: consultar un identificador existente y uno inexistente

### Tests for User Story 2

- [ ] T012 [US2] Añadir en `tests/api/v1/test_productos.py` los tests de la consulta individual: un id existente devuelve lo mismo que el listado (escenario 1); un id inexistente responde 404 con `{"detail": "Producto no encontrado"}` (escenario 2, FR-005); identificadores con caracteres inesperados, muy largos o numéricos responden el mismo 404 y nunca 422 (caso límite); el cuerpo del 404 no contiene el identificador recibido ni rutas de ficheros

### Implementation for User Story 2

- [ ] T013 [US2] Implementar `GET /productos/{id}` con `id: str` sin restricciones y `HTTPException(404, "Producto no encontrado")` en `src/app/api/v1/productos.py`

**Checkpoint**: las historias 1 y 2 funcionan por separado

---

## Phase 5: User Story 3 - Ver un precio actualizado tras un despliegue (Priority: P3)

**Goal**: tras desplegar un cambio de precio, la siguiente consulta devuelve el precio nuevo

**Independent Test**: arrancar la aplicación con un catálogo con un precio cambiado y comprobar ambas consultas

### Tests for User Story 3

- [ ] T014 [US3] Añadir en `tests/api/v1/test_productos.py` un test que crea la aplicación con una copia del catálogo en `tmp_path` con un precio modificado y comprueba que el listado y la consulta por id devuelven el precio nuevo (escenario 1, FR-009)

### Implementation for User Story 3

- [ ] T015 [US3] Comprobar que `src/app/api/v1/productos.py` lee siempre de `request.app.state.catalogo` y que no hay ninguna caché de respuestas; corregirlo si T014 falla

**Checkpoint**: las tres historias funcionan

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: observabilidad (FR-012) y verificación final

- [ ] T016 Escribir en `tests/test_observabilidad.py` los tests de FR-012: cada consulta a `/api/v1/productos` y a `/api/v1/productos/{id}` emite una línea de log JSON con `evento`, `metodo`, `ruta`, `estado` y `duracion_ms`; `ruta` es la plantilla y el log no contiene el identificador recibido; `GET /metrics` expone el contador por ruta y estado
- [ ] T017 Implementar el log JSON y las métricas (contador e histograma de `prometheus-client`) en `src/app/observabilidad.py`
- [ ] T018 Registrar el middleware de observabilidad para las rutas bajo `/api/` y exponer `GET /metrics` en `src/app/main.py`
- [ ] T019 Ejecutar `uv run pytest -q`, `uv run ruff check . && uv run ruff format --check .` y `uv run mypy src`, y corregir lo que falle
- [ ] T020 Validar los escenarios de `specs/001-catalogo-productos/quickstart.md` con la aplicación arrancada

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup y bloquea todas las historias
- **US1 (Phase 3)**: depende de Foundational
- **US2 (Phase 4)**: depende de Foundational; comparte fichero con US1, así que se hace después
- **US3 (Phase 5)**: depende de US1 y US2, porque comprueba ambas consultas
- **Polish (Phase 6)**: depende de que existan los dos endpoints

### Within Each User Story

- Los tests se escriben antes que la implementación y deben fallar primero
- Cada fase termina con sus tests en verde

### Parallel Opportunities

- T002 se puede hacer a la vez que T001
- T007 se puede hacer a la vez que T005 y T006
- El resto de tareas comparten ficheros (`main.py`, `productos.py`, `test_productos.py`) y van en serie

## Parallel Example: Foundational

```text
Task: "T006 Implementar los modelos en src/app/catalogo.py"
Task: "T007 Crear el catálogo de ejemplo en src/app/catalogo.json"
```

## Implementation Strategy

### MVP First (User Story 1)

1. Setup y Foundational
2. US1 y validar el listado: con eso la tienda ya puede dejar su JSON estático

### Incremental Delivery

1. US2 añade la ficha individual y el 404
2. US3 fija con un test el comportamiento ante un cambio de precio
3. Polish añade la observabilidad y la verificación final

Todo se entrega en un único PR (`Closes #5`), con un commit por fase.
