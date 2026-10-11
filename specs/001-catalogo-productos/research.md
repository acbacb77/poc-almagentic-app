# Research: Catálogo de productos

Decisiones de diseño que la spec deja al plan. No queda ningún `NEEDS CLARIFICATION`.

## 1. Forma del identificador

- **Decision**: cadena de texto opaca en formato slug (por ejemplo `cafe-molido-250g`). El parámetro de ruta se declara como `str` sin restricciones.
- **Rationale**: la spec pide que cualquier valor que no coincida con un producto reciba 404, sin distinguir errores de formato. Un parámetro `str` sin validación nunca produce un 422. Un slug es estable y legible en un fichero mantenido a mano.
- **Alternatives considered**: entero (FastAPI respondería 422 a `abc`, lo que contradice la spec); UUID (mismo problema y más incómodo de mantener a mano).

## 2. Representación del precio

- **Decision**: `Decimal` en el modelo, serializado en JSON como cadena con exactamente 2 decimales (`"12.50"`). En `catalogo.json` el precio también se escribe como cadena.
- **Rationale**: FR-004 exige exactamente 2 decimales. Un número JSON no lo garantiza (`12.50` se emite como `12.5`) y pasa por coma flotante. La cadena es la serialización por defecto de `Decimal` en Pydantic v2 y conserva los decimales.
- **Alternatives considered**: número JSON (pierde el cero final y la exactitud); entero en céntimos (no es "euros con 2 decimales" como pide el responsable).
- **Nota para la revisión**: es parte del contrato público de `/api/v1`; conviene que el responsable lo confirme en el PR antes de publicar.

## 3. Fichero y carga del catálogo

- **Decision**: `src/app/catalogo.json`, leído y validado una vez en `create_app()`. Si no es válido, la aplicación no arranca.
- **Rationale**: JSON se lee con la biblioteca estándar, sin dependencias. Cargar al arrancar cumple FR-009: no hay caché de respuestas y cada despliegue reinicia el proceso con el fichero nuevo. Fallar al arrancar, junto con un test que valida el fichero real, cumple FR-010: el error se detecta en CI y, en último caso, el despliegue no llega a servir tráfico.
- **Alternatives considered**: YAML (dependencia nueva); módulo Python con una lista (mezcla datos y código); releer el fichero en cada petición (trabajo innecesario y el error aparecería al atender una consulta, justo lo que la spec prohíbe).

## 4. Validación del catálogo

- **Decision**: modelos Pydantic estrictos. `Producto`: `id` y `nombre` no vacíos tras recortar espacios, `precio` no negativo y con exactamente 2 decimales, sin campos extra. `Catalogo`: entre 5 y 10 productos e identificadores únicos.
- **Rationale**: cubre todos los casos de FR-010 con un esquema explícito (constitución I).
- **Alternatives considered**: validación manual con `if` (más código y peor mensaje de error).

## 5. Respuesta 404

- **Decision**: `HTTPException(404, detail="Producto no encontrado")`.
- **Rationale**: es el formato por defecto de FastAPI que pide el responsable, con un mensaje fijo que no incluye el identificador recibido ni detalles internos.
- **Alternatives considered**: incluir el identificador en el mensaje (refleja entrada del cliente sin necesidad).

## 6. Observabilidad (FR-012)

- **Decision**: un middleware HTTP que, para las rutas bajo `/api/`, escribe una línea de log JSON (`evento`, `metodo`, `ruta`, `estado`, `duracion_ms`) con `logging` de la biblioteca estándar y actualiza un contador y un histograma de `prometheus-client`. Las métricas se exponen en `GET /metrics`, sin versionar, igual que `/health`.
- **Rationale**: `ruta` es la plantilla (`/api/v1/productos/{id}`), no la URL real: así no se registra entrada arbitraria del cliente ni se dispara la cardinalidad de las etiquetas. No se registran IP, cabeceras ni cuerpo, por lo que no hay datos personales. El formato de Prometheus es el estándar de facto y la biblioteca oficial evita escribirlo a mano.
- **Alternatives considered**: contadores propios y formato de texto escrito a mano (reimplementa una biblioteca estándar); OpenTelemetry (varias dependencias y un colector, excesivo para dos endpoints); solo logs (el anexo de la constitución pide también métricas).
- **Nota para la revisión**: `/metrics` es un endpoint operativo que la spec no enumera; se añade porque el anexo de la constitución exige exponer métricas.

## 7. Dependencias

Todas de PyPI, con versión fijada en `pyproject.toml` y en `uv.lock`.

| Paquete | Uso | Licencia |
|---|---|---|
| `fastapi` | framework (stack de `AGENTS.md`) | MIT |
| `uvicorn` | arranque local (comando de `AGENTS.md`) | BSD-3-Clause |
| `prometheus-client` | métricas (FR-012) | Apache-2.0 |
| `pytest` (dev) | tests | MIT |
| `httpx` (dev) | lo requiere `TestClient` de FastAPI | BSD-3-Clause |
| `ruff` (dev) | lint y formato | MIT |
| `mypy` (dev) | tipos | MIT |

## 8. Empaquetado

- **Decision**: proyecto `uv` sin empaquetar (`[tool.uv] package = false`). `pytest` usa `pythonpath = ["src"]` y `mypy` usa `mypy_path = "src"`.
- **Rationale**: coincide con el comando de arranque de `AGENTS.md` (`--app-dir src`) y evita configurar un backend de construcción que nadie necesita todavía.
- **Alternatives considered**: paquete instalable con `hatchling` (más configuración sin beneficio hoy).
