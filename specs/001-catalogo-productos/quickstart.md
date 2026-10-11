# Quickstart: Catálogo de productos

Guía para comprobar la feature de principio a fin. El contrato está en [contracts/openapi.yaml](./contracts/openapi.yaml) y las reglas de los datos en [data-model.md](./data-model.md).

## Requisitos

- Python 3.12 y `uv`

## Preparación

```bash
uv sync
```

## Comprobaciones automáticas

```bash
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run mypy src
```

Las cuatro deben terminar sin errores.

## Validación manual

```bash
uv run uvicorn app.main:app --reload --app-dir src
```

En otra terminal:

| Escenario | Comando | Resultado esperado |
|---|---|---|
| Salud | `curl -s localhost:8000/health` | `{"status":"ok"}` |
| Listado (US1) | `curl -s localhost:8000/api/v1/productos` | 200 y una lista de 5 a 10 productos con `id`, `nombre` y `precio` |
| Producto existente (US2) | `curl -s localhost:8000/api/v1/productos/cafe-molido-250g` | 200 y el mismo producto que en el listado |
| Producto inexistente (US2) | `curl -si localhost:8000/api/v1/productos/no-existe` | 404 y `{"detail":"Producto no encontrado"}` |
| Métricas (FR-012) | `curl -s localhost:8000/metrics` | contadores de las consultas anteriores, etiquetados por ruta y estado |

Cada consulta a `/api/v1/...` deja además una línea de log en JSON en la salida de `uvicorn`.

## Cambio de precio (US3)

1. Cambia el `precio` de un producto en `src/app/catalogo.json`.
2. Reinicia la aplicación (equivale a un despliegue).
3. Repite las consultas del listado y de ese producto: ambas devuelven el precio nuevo.

## Catálogo mal formado (FR-010)

Deja un producto con `"precio": "-1.00"` en `src/app/catalogo.json`:

- `uv run pytest -q` falla en `tests/test_catalogo.py`.
- La aplicación no arranca.

Deshaz el cambio al terminar.
