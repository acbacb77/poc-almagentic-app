# Feature Specification: Catálogo de productos

**Feature Branch**: `spec/5-catalogo-productos` (spec) → `feat/5-catalogo-productos` (implementación)

**Created**: 2026-10-04

**Status**: Draft

**Issue**: #5

**Input**: User description: "Un endpoint que devuelva el catálogo de productos (identificador, nombre y precio) para que la tienda web lo muestre, y que permita consultar un producto por id. Si el id no existe, responde 404." Completado con las respuestas del responsable en el issue #5.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar el catálogo completo (Priority: P1)

La tienda web pide el catálogo y recibe todos los productos, cada uno con su identificador, su nombre y su precio, para pintar el listado sin mantener una copia propia.

**Why this priority**: Es el motivo de la petición: la tienda deja de mantener el catálogo a mano en un JSON estático. Con solo esta historia la tienda ya puede mostrar el catálogo.

**Independent Test**: Se consulta `GET /api/v1/productos` sin credenciales y se comprueba que la respuesta contiene todos los productos del catálogo con identificador, nombre y precio.

**Acceptance Scenarios**:

1. **Given** que existen productos en el catálogo, **When** se consulta el listado, **Then** se devuelve la lista completa con el identificador, el nombre y el precio de cada producto.
2. **Given** que existen productos en el catálogo, **When** se consulta el listado sin ninguna credencial, **Then** la consulta se atiende igual que cualquier otra.
3. **Given** un producto del catálogo, **When** aparece en el listado, **Then** su precio está expresado en euros, con exactamente 2 decimales e IVA incluido.

---

### User Story 2 - Consultar un producto por su identificador (Priority: P2)

La tienda web pide un producto concreto por su identificador y recibe su identificador, su nombre y su precio, para mostrar la ficha de ese producto. Si el identificador no corresponde a ningún producto, recibe una respuesta de "no encontrado".

**Why this priority**: Completa la petición, pero la tienda ya obtiene valor con el listado; la ficha individual puede derivarse de él mientras tanto.

**Independent Test**: Se consulta `GET /api/v1/productos/{id}` con un identificador existente y con uno inexistente, y se comprueba que el primero devuelve el producto y el segundo responde 404.

**Acceptance Scenarios**:

1. **Given** un identificador que existe en el catálogo, **When** se consulta ese producto, **Then** se devuelve su identificador, su nombre y su precio, iguales a los que muestra el listado.
2. **Given** un identificador que no existe en el catálogo, **When** se consulta ese producto, **Then** la respuesta es 404 con un cuerpo de la forma `{"detail": "..."}` y un mensaje genérico.

---

### User Story 3 - Ver un precio actualizado tras un despliegue (Priority: P3)

El equipo cambia el precio de un producto en el catálogo mediante un PR. Una vez desplegado el cambio, la tienda web ve el precio nuevo en la siguiente consulta, sin ninguna acción adicional.

**Why this priority**: Es el segundo beneficio de la petición (que los cambios de precio lleguen a la tienda sin tocarla), pero depende de que las dos historias anteriores existan.

**Independent Test**: Se cambia el precio de un producto en el catálogo y, con el cambio aplicado, se comprueba que tanto el listado como la consulta por identificador devuelven el precio nuevo.

**Acceptance Scenarios**:

1. **Given** que se ha desplegado un cambio de precio de un producto, **When** la tienda web vuelve a consultar el listado o ese producto, **Then** la respuesta contiene el precio nuevo.

---

### Edge Cases

- **Identificador que no corresponde a ningún producto, sea cual sea su forma** (vacío de significado, con caracteres inesperados, muy largo): la respuesta es 404 con el mismo cuerpo `{"detail": "..."}`; no se distingue entre "formato no válido" y "no existe".
- **Dos consultas seguidas sin despliegue entre medias**: devuelven exactamente los mismos datos y en el mismo orden.
- **Catálogo mal formado** (producto sin nombre, precio negativo o con más de 2 decimales, identificadores repetidos): es un error del equipo que mantiene el catálogo y debe detectarse antes de que el cambio llegue a la tienda, no al atender una consulta.
- **Mensaje del 404**: no revela detalles internos (rutas de ficheros, trazas ni el contenido del catálogo).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE ofrecer la consulta del catálogo completo en `GET /api/v1/productos`, que devuelve todos los productos.
- **FR-002**: El sistema DEBE ofrecer la consulta de un producto en `GET /api/v1/productos/{id}`, que devuelve el producto cuyo identificador coincide con `{id}`.
- **FR-003**: Cada producto devuelto DEBE incluir exactamente su identificador, su nombre y su precio, tanto en el listado como en la consulta individual, y con los mismos valores en ambas.
- **FR-004**: El precio DEBE expresarse en euros, con exactamente 2 decimales e IVA incluido.
- **FR-005**: Cuando el identificador consultado no corresponde a ningún producto, el sistema DEBE responder 404 con un cuerpo de la forma `{"detail": "..."}` y un mensaje genérico que no exponga detalles internos.
- **FR-006**: Ambas consultas DEBEN ser públicas: se atienden sin autenticación.
- **FR-007**: El catálogo DEBE ser una lista fija de entre 5 y 10 productos mantenida en un fichero del repositorio; el equipo lo modifica mediante un PR.
- **FR-008**: El listado DEBE devolver siempre el catálogo completo, sin paginación ni filtros, y en un orden estable entre consultas.
- **FR-009**: El sistema NO DEBE cachear respuestas: tras desplegar un cambio en el catálogo, la siguiente consulta refleja los datos nuevos.
- **FR-010**: Un catálogo mal formado (identificadores repetidos, nombre vacío, precio negativo o con más de 2 decimales, menos de 5 o más de 10 productos) DEBE detectarse antes de que el cambio se publique, de modo que nunca se sirva a la tienda.
- **FR-011**: Las rutas de esta feature forman parte de la versión publicada `/api/v1` y, una vez publicadas, NO DEBEN cambiar de forma incompatible.
- **FR-012**: Cada una de las dos consultas DEBE dejar métricas y logs estructurados de su uso, sin datos personales (anexo de la constitución).

### Key Entities

- **Producto**: artículo que la tienda web muestra. Atributos: identificador (único dentro del catálogo y estable en el tiempo), nombre (texto no vacío) y precio (importe en euros, no negativo, con 2 decimales e IVA incluido).
- **Catálogo**: conjunto fijo de 5 a 10 productos que el equipo mantiene en el repositorio. Solo cambia con un PR y un despliegue.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La tienda web obtiene el 100 % de los productos del catálogo, con identificador, nombre y precio, en una sola consulta.
- **SC-002**: El 100 % de las consultas por un identificador existente devuelven ese producto, y el 100 % de las consultas por un identificador inexistente reciben la respuesta "no encontrado".
- **SC-003**: Tras desplegar un cambio de precio, la primera consulta posterior ya muestra el precio nuevo, sin ningún cambio en la tienda web.
- **SC-004**: La tienda web deja de mantener su copia estática del catálogo: los cambios de catálogo se hacen en un único sitio.
- **SC-005**: La tienda web recibe el catálogo lo bastante rápido como para pintar el listado sin espera perceptible (menos de 1 segundo por consulta).

## Assumptions

- **Forma del identificador**: el issue no la fija. Se asume que el identificador es un valor opaco para la tienda, único y estable, y que cualquier valor que no coincida con un producto recibe 404 (no se distingue un error de formato). El tipo concreto se decide en el plan.
- **Contenido inicial del catálogo**: el issue no enumera los productos. Se asume que la implementación incluye un catálogo de ejemplo de 5 a 10 productos que el equipo ajustará después por PR.
- **Moneda**: todos los precios están en euros, así que la respuesta no incluye un campo de moneda; el issue pide solo identificador, nombre y precio.
- **Orden del listado**: el issue no pide un orden concreto; se asume el orden en que el equipo mantiene el catálogo.
- **"Al momento"**: según la aclaración del responsable, un cambio de precio llega con un despliegue; no hay actualización en caliente.
- **Caché en la tienda**: lo que cachee la tienda web o cualquier intermediario queda fuera del control de esta feature; aquí solo se garantiza que la API no cachea.
- **Fuera de alcance**: base de datos, paginación, filtros, búsqueda, autenticación, y crear, modificar o borrar productos a través de la API.
- **Dependencia**: a fecha de esta spec el repositorio aún no contiene la aplicación base (`src/`, `tests/`, `pyproject.toml`). La implementación de esta feature necesita ese esqueleto; el plan debe decidir si lo crea o si llega por otro issue.
- El issue #6 no está relacionado con esta petición.
