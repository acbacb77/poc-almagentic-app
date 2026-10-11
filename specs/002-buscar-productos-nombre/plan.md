# Implementation Plan: Buscar productos del catálogo por nombre

**Branch**: `feat/18-buscar-productos-nombre` | **Date**: 2026-10-11 | **Spec**: [spec.md](./spec.md)

**Issue**: #18

## Summary

Se añade el parámetro opcional `q` a `GET /api/v1/productos`. Con texto, el listado devuelve los productos cuyo nombre contiene `q`, sin distinguir mayúsculas ni acentos, conservando el orden del catálogo. Sin `q` (o vacío) el comportamiento no cambia. El filtrado es en memoria sobre el catálogo existente.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: las existentes (FastAPI, Pydantic v2, prometheus-client); sin dependencias nuevas

**Storage**: N/A (catálogo JSON en memoria)

**Testing**: pytest con `TestClient`

**Project Type**: web-service

**Performance Goals**: menos de 1 s (SC-005); catálogo de 5 a 10 productos

**Constraints**: `q` es texto literal (sin comodines ni consultas), máximo 100 caracteres tras `strip`, errores 422 genéricos, el texto de `q` nunca se registra

## Constitution Check

| Principio | Cómo se cumple | Estado |
|---|---|---|
| I. Seguridad por defecto | `q` se valida con longitud máxima y se usa solo en una comparación de subcadena en memoria. El 422 lleva un mensaje fijo, sin eco de la entrada. | PASA |
| II. Spec primero | Issue #18 y spec fusionada (#19). | PASA |
| III. Tests como contrato | Cada escenario y caso límite tiene test. | PASA |
| IV. Trazabilidad | Rama `feat/18-...`, `Refs #18`, PR con `Closes #18`. | PASA |
| V. Control humano | PR aprobado por un humano; sin tocar ficheros de gobierno. | PASA |
| VI. Simplicidad | Una función de normalización y un método de filtrado; sin dependencias. | PASA |
| Anexo: compatibilidad | Parámetro opcional en `/api/v1`; sin `q` la respuesta no cambia. | PASA |
| Anexo: observabilidad | Evento de log `busqueda` con solo `longitud_q` y `resultados`, y contador de búsquedas por resultado; nunca el texto de `q`. | PASA |

## Project Structure

```text
specs/002-buscar-productos-nombre/   # spec, plan, research, contracts, quickstart, tasks
src/app/catalogo.py                  # normalizar() y Catalogo.buscar_por_nombre()
src/app/api/v1/productos.py          # parámetro q, validación, log y métrica
src/app/observabilidad.py            # contador y log de búsquedas
tests/test_catalogo.py               # normalización y filtrado
tests/api/v1/test_busqueda.py        # criterios de aceptación y casos límite por HTTP
tests/test_observabilidad.py         # log y métrica de búsqueda (FR-011)
```

## Design

- **Normalización**: `NFD`, eliminar marcas combinantes, `casefold()`. Se aplica a `q` (tras `strip`) y a cada nombre; coincidencia con `in`. Cubre formas Unicode precompuestas y descompuestas y trata `%`, `_`, `*` como texto.
- **Validación**: `q: str | None = Query(None)`; tras `strip`, vacío → ausente; más de 100 caracteres → `HTTPException(422, "Parámetro q no válido")` (mensaje genérico sin eco, FR-012). Con `q` repetido FastAPI usa un solo valor.
- **Observabilidad**: solo cuando hay búsqueda efectiva se emite el log `{"evento": "busqueda", "longitud_q", "resultados"}` en el logger `app.consultas`, y se incrementa `app_busquedas_total{resultado="con_resultados"|"sin_resultados"}`. El log de consulta existente no cambia.

**Revisión tras el diseño**: sin violaciones.
