# Feature Specification: Retirar la API v1 del catálogo

**Feature Branch**: `spec/40-retirar-api-v1` (spec) → `feat/40-retirar-api-v1` (implementación)

**Created**: 2026-10-25

**Status**: Draft

**Issue**: #40

**Input**: User description: "Retirar /api/v1/productos y /api/v1/productos/{id} (y las specs correspondientes). Todas las rutas de v1 responden 410 Gone con un mensaje genérico, la cabecera Link hacia su equivalente en v2 (rel=\"successor-version\") y las mismas cabeceras Deprecation y Sunset. v2 y /health no cambian. Decisión: se retira antes del Sunset anunciado (28-10-2026). Es staging, no hay clientes externos y el responsable ha comprobado que nadie usa v1. Se acepta no cumplir la fecha anunciada." Completado con las respuestas del responsable en el issue #40: la ruta v2 equivalente es la misma ruta cambiando `v1` por `v2`; `Deprecation` y `Sunset` mantienen los valores anunciados; el 410 se aplica a todos los métodos; el adelanto está comunicado y confirmado.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Los clientes rezagados de v1 saben que ya no existe y dónde ir (Priority: P1)

Un cliente que todavía llama a v1 recibe, en lugar de datos, una respuesta clara de que el recurso ha sido retirado, con un mensaje genérico y la indicación de la ruta equivalente en v2.

**Why this priority**: Es el núcleo de la petición: dejar de mantener v1 sin que los rezagados se queden sin pista.

**Independent Test**: Se hace `GET /api/v1/productos`, `GET /api/v1/productos?q=ab` y `GET /api/v1/productos/{id}` y se comprueba que todas devuelven 410 con mensaje genérico y `Link` hacia la ruta v2 equivalente.

**Acceptance Scenarios**:

1. **Given** la API desplegada, **When** se consulta `GET /api/v1/productos`, **Then** la respuesta es 410 con un cuerpo `{"detail": "..."}` de mensaje genérico y ningún dato del catálogo.
2. **Given** la API desplegada, **When** se consulta `GET /api/v1/productos/{id}` (exista o no el id), **Then** la respuesta es 410, nunca 200 ni 404.
3. **Given** una respuesta 410 de v1, **When** se inspeccionan sus cabeceras, **Then** incluye `Link: <ruta v2>; rel="successor-version"`, donde la ruta v2 es la misma ruta de la petición cambiando `v1` por `v2` (`/api/v2/productos`, `/api/v2/productos/{id}`).
4. **Given** una consulta a `GET /api/v1/productos?q=…`, **When** se recibe el 410, **Then** el `Link` conserva `q` (codificado), igual que durante la obsolescencia.
5. **Given** una respuesta 410 de v1, **When** se inspeccionan sus cabeceras, **Then** lleva `Deprecation: @1792969200` y `Sunset: Wed, 28 Oct 2026 23:00:00 GMT`, los mismos valores que ya se anunciaban (spec 004, FR-010 y FR-012).

---

### User Story 2 - Todo lo que cuelga de v1 está retirado, sea cual sea el método o la ruta (Priority: P1)

Ninguna ruta bajo `/api/v1/`, ni ningún método HTTP, da una respuesta distinta de 410: no quedan huecos en los que v1 siga respondiendo o dé errores distintos.

**Why this priority**: Si quedara alguna ruta o método vivo, v1 seguiría teniendo que mantenerse y la retirada no cumpliría su objetivo.

**Independent Test**: Se llama a `/api/v1/productos`, `/api/v1/productos/{id}` y a una ruta inexistente como `/api/v1/otra-cosa` con GET, POST, PUT, PATCH, DELETE, HEAD y OPTIONS, y se comprueba 410 en todos los casos.

**Acceptance Scenarios**:

1. **Given** cualquier método HTTP (GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS), **When** se llama a una ruta de v1, **Then** la respuesta es 410 con las mismas cabeceras (`Deprecation`, `Sunset`, `Link`).
2. **Given** una ruta bajo `/api/v1/` que nunca existió (por ejemplo `/api/v1/otra-cosa`), **When** se consulta, **Then** la respuesta es 410 y no 404, con el `Link` a la misma ruta en v2.
3. **Given** un `q` de más de 200 caracteres o cualquier otro parámetro inválido en una llamada a v1, **When** se consulta, **Then** la respuesta es 410 y no 422: ya no se valida nada en v1.
4. **Given** cualquier llamada a v1, **When** se responde, **Then** el cuerpo no repite texto recibido (ni la ruta, ni `q`, ni el `id`).

---

### User Story 3 - v2 y /health siguen exactamente igual (Priority: P1)

Los clientes de v2 y los sistemas que vigilan `GET /health` no notan ningún cambio.

**Why this priority**: La retirada no puede romper lo que sí está vigente; es la contrapartida de poder quitar v1.

**Independent Test**: La suite de tests de v2 y de `/health` pasa sin modificar ni una línea.

**Acceptance Scenarios**:

1. **Given** el catálogo, **When** se consulta `GET /api/v2/productos` (con o sin `q`) y `GET /api/v2/productos/{id}`, **Then** las respuestas son idénticas en código, cuerpo y cabeceras a las anteriores a este cambio (spec 004).
2. **Given** la API, **When** se consulta `GET /health`, **Then** responde `{"status": "ok"}` sin autenticación y sin cabeceras `Deprecation`, `Sunset` ni `Link` de sucesión.
3. **Given** una respuesta de v2 o de `/health`, **When** se inspeccionan sus cabeceras, **Then** no hay rastro de la retirada de v1.

---

### User Story 4 - Ver en el panel que v1 solo recibe 410 (Priority: P2)

Quien opera el servicio abre el panel «Consultas por versión de la API» y comprueba que el tráfico de v1 solo muestra respuestas 410, y puede confirmar así que no queda ningún consumidor.

**Why this priority**: Es un criterio de hecho de la petición y la forma de detectar a un cliente no localizado, pero la retirada funciona sin él.

**Independent Test**: Se hacen llamadas a v1 (varios métodos y rutas) y a v2, y se comprueba en las métricas que las de v1 se contabilizan como versión v1 con código 410 y las de v2 siguen separadas.

**Acceptance Scenarios**:

1. **Given** llamadas a cualquier ruta o método de v1, **When** se leen las métricas de consultas, **Then** se contabilizan bajo la versión v1 con código 410, sin ningún otro código.
2. **Given** llamadas a v2, **When** se leen las métricas, **Then** su contabilización no cambia respecto a la spec 004.
3. **Given** llamadas a rutas v1 inexistentes o con valores arbitrarios en la ruta, **When** se leen las métricas, **Then** no se crea una serie nueva por cada valor distinto (el número de series no crece con la entrada del cliente).

---

### User Story 5 - Las specs y la documentación dejan de presentar v1 como API activa (Priority: P2)

Quien lea el repositorio o la documentación de la API no ve v1 como una API vigente, sino como retirada.

**Why this priority**: Evita que alguien implemente contra v1 o la tome por vigente, pero no afecta al comportamiento en ejecución.

**Independent Test**: Se revisan las specs 001, 002 y 003 y la documentación generada de la API y se comprueba que v1 figura como retirada y no como contrato activo.

**Acceptance Scenarios**:

1. **Given** las specs que definen v1 (001, 002 y 003), **When** se revisa el repositorio tras el cambio, **Then** cada una indica en su cabecera que v1 está retirada por esta spec; se conservan como histórico y como referencia de las reglas que v2 reutiliza (specs 002 y 003).
2. **Given** la documentación de la API generada por la aplicación, **When** se consulta, **Then** no publica los endpoints de v1 como operaciones activas.

---

### Edge Cases

- **Después del `Sunset`**: el 410 sigue devolviendo las mismas cabeceras con las mismas fechas fijas; no dependen de cuándo se consulte.
- **HEAD y OPTIONS**: devuelven 410 con las cabeceras como el resto de métodos, sin cuerpo en HEAD.
- **Rutas v1 con barra final, mayúsculas o subrutas** (`/api/v1/productos/`, `/api/v1/productos/a/b`): cualquier ruta que empiece por `/api/v1/` da 410.
- **Prefijos parecidos** (`/api/v10/…`, `/api/v1x`): no son v1 y se comportan como hasta ahora.
- **Caracteres especiales en la ruta o en `q`**: se codifican en el `Link` para que la URL sea válida y no permiten inyectar otras cabeceras ni destinos.
- **Ruta v1 sin equivalente real en v2** (`/api/v1/otra-cosa`): el `Link` sigue la misma regla de sustitución aunque el destino no exista en v2.
- **Cuerpo sin eco**: ni el 410 ni los logs repiten el texto de `q`, del `id` ni de la ruta recibida (constitución, principio I; spec 002, FR-011).
- **Adelanto sobre el `Sunset`**: v1 deja de funcionar antes de la fecha anunciada; ver Supuestos.

## Requirements *(mandatory)*

### Functional Requirements

**Retirada de v1**

- **FR-001**: Toda petición cuya ruta empiece por `/api/v1/`, con cualquier método HTTP, DEBE responder 410 Gone, incluidas las rutas que nunca existieron.
- **FR-002**: El cuerpo del 410 DEBE ser `{"detail": "<mensaje genérico>"}`, con el mismo formato de error que el resto de la API. El mensaje indica que el recurso está retirado, sin datos del catálogo ni detalles internos, y NO DEBE incluir texto recibido en la petición (ruta, `q`, `id`).
- **FR-003**: v1 NO DEBE devolver nunca datos del catálogo ni ningún código distinto de 410 (ni 200, ni 404, ni 405, ni 422) para rutas bajo `/api/v1/`.
- **FR-004**: Se DEBE eliminar el comportamiento de v1 (consulta, búsqueda y su validación de `q`); no queda lógica de v1 que mantener salvo la respuesta 410.

**Cabeceras de la respuesta 410**

- **FR-005**: Toda respuesta 410 de v1 DEBE llevar `Deprecation: @1792969200` y `Sunset: Wed, 28 Oct 2026 23:00:00 GMT`, los valores ya anunciados en la spec 004 (FR-010 y FR-012). Son fijos y no dependen de la fecha de la consulta ni del despliegue.
- **FR-006**: Toda respuesta 410 de v1 DEBE llevar `Link: <ruta v2>; rel="successor-version"`, donde `<ruta v2>` es la ruta recibida con `/api/v1/` sustituido por `/api/v2/` (`/api/v1/productos` → `/api/v2/productos`; `/api/v1/productos/{id}` → `/api/v2/productos/{id}`).
- **FR-007**: Si la petición lleva `q`, el `Link` DEBE conservarlo, como hacía la spec 004 (FR-011). Los valores trasladados desde la petición DEBEN codificarse para producir una URL válida y no permitir inyección de cabeceras ni de otros destinos.
- **FR-008**: Las respuestas de v1 NO DEBEN poder guardarse en cachés compartidas: se mantiene `Cache-Control: no-store` en todas las rutas bajo `/api/`.

**Lo que no cambia**

- **FR-009**: v2 (`/api/v2/productos`, `/api/v2/productos/{id}`) y `GET /health` NO DEBEN cambiar en comportamiento, códigos, cuerpos ni cabeceras (specs 001 a 004). Sus respuestas NO DEBEN llevar `Deprecation`, `Sunset` ni `Link` de sucesión.
- **FR-010**: Las rutas que no empiezan por `/api/v1/` (incluidos prefijos parecidos como `/api/v10/`) NO DEBEN cambiar de comportamiento.

**Observabilidad y seguridad**

- **FR-011**: Las métricas de consultas DEBEN seguir distinguiendo la versión de la API y contabilizar todas las llamadas a v1 como versión v1 con código 410, de modo que el panel «Consultas por versión de la API» muestre para v1 solo respuestas 410.
- **FR-012**: Las métricas NO DEBEN generar series nuevas según la ruta, el `id` o el `q` recibidos en rutas v1 inexistentes o arbitrarias (cardinalidad acotada).
- **FR-013**: Los logs de las llamadas a v1 DEBEN ser estructurados y sin datos personales, y NO DEBEN contener el texto de `q`, el `id` ni la ruta recibida más allá de la versión y el código de estado.

**Pruebas, specs y documentación**

- **FR-014**: Los tests que verifican el comportamiento de v1 (listado, búsqueda, detalle, errores 404 y 422, cabeceras de obsolescencia) DEBEN sustituirse por tests de la respuesta 410 (código, mensaje genérico, cabeceras y cobertura de métodos y rutas). Los tests de v2 y de `/health` NO DEBEN modificarse y deben seguir pasando.
- **FR-015**: Las specs 001, 002 y 003 DEBEN indicar en su cabecera que v1 está retirada por la spec 005, sin borrarse: se conservan como histórico y como fuente de las reglas que v2 reutiliza. La spec 004 se conserva sin cambios de contenido.
- **FR-016**: La documentación de la API generada por la aplicación NO DEBE publicar los endpoints de v1 como operaciones activas.

### Key Entities

- **Respuesta de retirada**: respuesta 410 que sustituye a toda respuesta de v1; formada por el mensaje genérico y tres cabeceras (`Deprecation`, `Sunset`, `Link` de sucesión).
- **Ruta equivalente en v2**: la misma ruta de la petición con `v2` en lugar de `v1`; es el destino del `Link`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las llamadas a rutas bajo `/api/v1/`, con cualquier método, devuelve 410.
- **SC-002**: El 100 % de las respuestas 410 lleva `Deprecation`, `Sunset` y un `Link` con `rel="successor-version"` hacia la ruta v2 equivalente, con los valores indicados en esta spec.
- **SC-003**: El 0 % de las respuestas de v1 contiene datos del catálogo o texto recibido del cliente.
- **SC-004**: Las respuestas de v2 y de `/health` son idénticas a las anteriores al cambio en el 100 % de los casos probados, y sus tests pasan sin modificarse.
- **SC-005**: Tras desplegar, el panel «Consultas por versión de la API» muestra para v1 únicamente respuestas 410.
- **SC-006**: En ningún log ni métrica de v1 aparece el texto de `q`, el `id` ni la ruta recibida.
- **SC-007**: Una persona que migra un cliente de v1 a v2 puede hallar el destino correcto solo con la respuesta 410 recibida, sin consultar documentación adicional.

## Assumptions

- **Ruta equivalente** (respuesta del responsable): es la misma ruta con `v2` en lugar de `v1`; se aplica la misma sustitución a cualquier ruta bajo `/api/v1/`, aunque el destino no exista en v2.
- **Cabeceras** (respuesta del responsable): se mantienen `Deprecation` y `Sunset` con los valores de la spec 004, incluida la fecha de `Sunset` del 28-10-2026, aunque la retirada se adelante a ella.
- **Métodos** (respuesta del responsable): el 410 se aplica a todos los métodos, no solo a GET.
- **Aviso del adelanto** (respuesta del responsable): el responsable confirma que el adelanto está comunicado y que nadie usa v1. Es un entorno de staging de la POC sin clientes externos.
- **Aviso previo de la constitución**: el anexo exige retirar con aviso previo (`Deprecation`, `Sunset`) y una spec de retirada. Esta spec es la de retirada, pero el aviso lleva activo solo desde la spec 004 y la retirada ocurre antes del `Sunset` anunciado. El responsable lo acepta de forma expresa; se señala aquí el conflicto con el principio para que quede trazado y quien apruebe el PR lo confirme.
- **Orden de entrega**: esta spec asume que la spec 004 (v2 y avisos en v1) ya está implementada y desplegada; sin v2 no tiene sentido el `Link`.
- **Reversibilidad**: la retirada se puede revertir con un revert del PR si apareciera un consumidor no detectado; se recomienda confirmar con el panel que nadie usa v1 antes del despliegue.
- **Panel de métricas**: «Consultas por versión de la API» se alimenta de las métricas de la aplicación. Esta spec exige que las métricas etiqueten bien versión y código; la configuración del panel y las alertas viven fuera de este repositorio y no se modifican aquí.
- **Fuera de alcance**: cambios en v2 o `/health`, autenticación, nuevas versiones, cambios en el contenedor (`Dockerfile`, `.dockerignore`) o el despliegue, y el borrado de las specs históricas.
- El issue #6 aparece como relacionado en el triage, pero nada indica que condicione esta spec.
