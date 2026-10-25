# Feature Specification: Catálogo v2 con importe y moneda, y v1 obsoleta

**Feature Branch**: `spec/36-catalogo-v2-precio-moneda` (spec) → `feat/36-catalogo-v2-precio-moneda` (implementación)

**Created**: 2026-10-25

**Status**: Draft

**Issue**: #36

**Input**: User description: "Una versión 2 del catálogo (`/api/v2/productos` y `/api/v2/productos/{id}`, con la misma búsqueda por `q`) en la que el precio lleve importe y moneda: `\"precio\": {\"importe\": \"12.50\", \"moneda\": \"EUR\"}`. El importe es texto decimal con exactamente 2 decimales y la moneda un código ISO 4217. A la vez, v1 pasa a estar obsoleta: todas sus respuestas llevan `Deprecation`, `Sunset` y `Link` (`rel=\"successor-version\"`) hacia su equivalente en v2. v1 sigue funcionando igual hasta su retirada, que irá en otra petición." Completado con las respuestas del responsable en el issue #36.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar el catálogo v2 con precio estructurado (Priority: P1)

La tienda web (o cualquier cliente que muestre precios en otra moneda) consulta el catálogo en v2 y recibe cada producto con su identificador, su nombre y un precio formado por un importe y una moneda, para poder mostrarlo o convertirlo sin errores de redondeo.

**Why this priority**: Es el valor central de la petición: sin v2 no se puede vender en varias monedas.

**Independent Test**: Se consulta `GET /api/v2/productos` y `GET /api/v2/productos/{id}` sin credenciales y se comprueba que el precio es un objeto con `importe` (texto con 2 decimales) y `moneda` (`"EUR"`).

**Acceptance Scenarios**:

1. **Given** que existen productos en el catálogo, **When** se consulta `GET /api/v2/productos`, **Then** se devuelve la lista completa, y cada producto tiene `id`, `nombre` y `precio` con la forma `{"importe": "12.50", "moneda": "EUR"}`.
2. **Given** un identificador existente, **When** se consulta `GET /api/v2/productos/{id}`, **Then** se devuelve ese producto con los mismos valores que muestra el listado v2.
3. **Given** un producto cuyo precio en v1 es 12,5, **When** se consulta en v2, **Then** el importe es el texto `"12.50"`: el mismo valor, sin redondeo ni conversión, siempre con exactamente 2 decimales.
4. **Given** cualquier producto del catálogo actual, **When** se consulta en v2, **Then** la moneda es `"EUR"`, tomada del dato del catálogo y no calculada.
5. **Given** cualquier producto, **When** se compara su respuesta v2 con la de v1, **Then** `id` y `nombre` son idénticos y solo cambia la forma de `precio`.

---

### User Story 2 - Buscar y recibir errores en v2 igual que en v1 (Priority: P1)

Un cliente busca por nombre en v2 con el mismo parámetro `q` y obtiene las mismas coincidencias y los mismos errores que en v1, solo que con el precio en formato v2.

**Why this priority**: La migración debe ser un cambio de ruta y de forma del precio, nada más. Sin paridad, los clientes tendrían que reescribir su lógica.

**Independent Test**: Para varios valores de `q` (con coincidencias, sin ellas, vacío, de 200 y de 201 caracteres) y para un id inexistente, se comparan las respuestas de v1 y v2.

**Acceptance Scenarios**:

1. **Given** un texto `q`, **When** se consulta `GET /api/v2/productos?q=…`, **Then** se devuelven los mismos productos, en el mismo orden, que en v1 con ese `q` (reglas de la spec 002), con el precio en formato v2.
2. **Given** un `q` vacío o de solo espacios, **When** se consulta v2, **Then** se devuelve el catálogo completo, igual que en v1.
3. **Given** un `q` de más de 200 caracteres tras quitar los espacios de los extremos, **When** se consulta v2, **Then** la respuesta es 422 con el mismo mensaje genérico que v1 (specs 002 y 003).
4. **Given** un identificador inexistente, **When** se consulta `GET /api/v2/productos/{id}`, **Then** la respuesta es 404 con el mismo cuerpo que en v1.
5. **Given** una búsqueda en v2, **When** se registra su uso, **Then** el log solo contiene la longitud de `q` y el número de resultados, nunca el texto (spec 002, FR-011).

---

### User Story 3 - Avisar a los clientes de v1 de que está obsoleta (Priority: P1)

Los clientes que usan v1 reciben en cada respuesta las cabeceras estándar que indican que v1 está obsoleta, cuándo se retirará y dónde está su equivalente en v2, sin que cambie nada más de la respuesta.

**Why this priority**: Es la mitad de la petición y lo que permite avisar con tiempo sin romper a nadie. Se entrega junto con v2 porque las cabeceras apuntan a ella.

**Independent Test**: Se consultan los endpoints de v1 (éxito, búsqueda, 404, 422) y se comprueba que cada respuesta lleva las tres cabeceras y que el cuerpo y el código de estado son los de antes.

**Acceptance Scenarios**:

1. **Given** cualquier respuesta de v1, **When** el cliente la recibe, **Then** incluye `Deprecation: @1792969200`, `Sunset: Wed, 28 Oct 2026 23:00:00 GMT` y un `Link` con `rel="successor-version"`.
2. **Given** una consulta a `GET /api/v1/productos` (con o sin `q`), **When** se recibe la respuesta, **Then** el `Link` apunta a `/api/v2/productos`, conservando el `q` recibido.
3. **Given** una consulta a `GET /api/v1/productos/{id}`, **When** se recibe la respuesta, **Then** el `Link` apunta a `/api/v2/productos/{id}` del mismo identificador.
4. **Given** una respuesta de error de v1 (404 por id inexistente, 422 por `q` demasiado largo), **When** se recibe, **Then** lleva también las tres cabeceras.
5. **Given** cualquier consulta a v1, **When** se compara con el comportamiento anterior a este cambio, **Then** el código de estado y el cuerpo son idénticos; solo se añaden las cabeceras.
6. **Given** una respuesta de v2 o de `GET /health`, **When** se recibe, **Then** no lleva `Deprecation`, `Sunset` ni `Link` de sucesión.

---

### User Story 4 - Ver el tráfico de v2 separado del de v1 (Priority: P2)

Quien opera el servicio abre el panel «Consultas por versión de la API» y ve el tráfico de v2 diferenciado del de v1, para seguir la migración de los clientes.

**Why this priority**: Es un criterio de hecho de la petición y sirve para decidir cuándo retirar v1, pero la API funciona sin él.

**Independent Test**: Se hacen consultas a v1 y a v2 y se comprueba que las métricas de consultas permiten distinguir la versión (la ruta v2 aparece como tal y no se mezcla con v1).

**Acceptance Scenarios**:

1. **Given** consultas a v1 y a v2, **When** se leen las métricas y se consulta el panel, **Then** el tráfico de cada versión aparece por separado.
2. **Given** un endpoint de v2, **When** atiende una consulta, **Then** deja métricas y logs estructurados sin datos personales (anexo de la constitución).

---

### Edge Cases

- **Respuestas de error de v1**: 404 y 422 también llevan las tres cabeceras, y su cuerpo no cambia.
- **Rutas v1 inexistentes** (por ejemplo `/api/v1/otra-cosa`): no corresponden a ningún endpoint de v1; el comportamiento es el actual y no se les exige ninguna cabecera.
- **`Link` y caracteres especiales**: el identificador o el `q` que se trasladan al `Link` van codificados para que la URL sea válida y no permitan inyectar otras cabeceras ni otros destinos.
- **Texto de `q` y privacidad**: el `Link` de v1 conserva `q` en la respuesta, pero `q` no se escribe en ningún log ni métrica (spec 002, FR-011).
- **Identificador con forma extraña**: sigue dando 404 genérico en ambas versiones, sin distinguir formato no válido de inexistente (spec 001).
- **Importe con menos decimales en origen** (12,5 o 12): el importe v2 siempre se muestra con 2 decimales (`"12.50"`, `"12.00"`).
- **Catálogo mal formado** (precio con más de 2 decimales): ya se rechaza antes de publicar (spec 001, FR-010); v2 no necesita redondear.

## Requirements *(mandatory)*

### Functional Requirements

**Catálogo v2**

- **FR-001**: El sistema DEBE ofrecer `GET /api/v2/productos`, que devuelve todos los productos, y `GET /api/v2/productos/{id}`, que devuelve el producto con ese identificador.
- **FR-002**: Cada producto de v2 DEBE tener exactamente `id`, `nombre` y `precio`; `id` y `nombre` son los mismos que en v1.
- **FR-003**: `precio` DEBE ser un objeto con exactamente dos campos: `importe` y `moneda`.
- **FR-004**: `importe` DEBE ser un texto decimal con punto como separador y exactamente 2 decimales (por ejemplo `"12.50"`, `"3.00"`), sin separador de miles ni símbolo de moneda. Es el valor del catálogo escrito como texto: no hay redondeo ni conversión.
- **FR-005**: `moneda` DEBE ser un código ISO 4217 de tres letras mayúsculas. Es un dato de cada producto en el catálogo (no un valor fijo del endpoint ni calculado) y hoy es `"EUR"` en todos los productos.
- **FR-006**: El listado v2 DEBE aceptar el parámetro opcional `q` con las mismas reglas que v1: coincidencia por fragmento sin distinguir mayúsculas ni acentos, `q` vacío o de solo espacios equivale a ausente, máximo de 200 caracteres tras quitar espacios de los extremos (specs 002 y 003) y mismo orden de resultados.
- **FR-007**: v2 DEBE devolver los mismos errores que v1 para los mismos casos: 404 con cuerpo `{"detail": "..."}` genérico para un identificador inexistente de cualquier forma, y 422 con el mismo mensaje genérico para un `q` demasiado largo, sin detalles internos.
- **FR-008**: Ambas consultas de v2 DEBEN ser públicas (sin autenticación) y NO DEBEN cachear respuestas, igual que v1 (spec 001, FR-006 y FR-009).
- **FR-009**: Para un mismo estado del catálogo, v1 y v2 DEBEN mostrar los mismos productos con el mismo valor de precio; solo difiere su representación.

**v1 obsoleta**

- **FR-010**: Toda respuesta de los endpoints de v1 (`/api/v1/productos` y `/api/v1/productos/{id}`), incluidas las de error, DEBE llevar tres cabeceras:
  - `Deprecation: @1792969200` (RFC 9745; 26-10-2026 00:00, hora de Madrid).
  - `Sunset: Wed, 28 Oct 2026 23:00:00 GMT` (RFC 8594; fin del 28 de octubre, hora de Madrid).
  - `Link: <ruta v2 equivalente>; rel="successor-version"`.
- **FR-011**: El destino de `Link` DEBE ser el recurso equivalente de v2: `/api/v2/productos` para el listado (conservando `q` si se envió) y `/api/v2/productos/{id}` para el detalle (con el mismo `id`). Los valores trasladados desde la petición DEBEN codificarse para producir una URL válida.
- **FR-012**: Las fechas de `Deprecation` y `Sunset` son valores fijos de esta spec; no dependen de cuándo se consulte ni de la fecha de despliegue.
- **FR-013**: Salvo las tres cabeceras, las respuestas de v1 NO DEBEN cambiar: mismos códigos de estado, mismo cuerpo, mismo orden, mismas reglas de búsqueda (anexo de la constitución: una versión publicada no cambia de forma incompatible).
- **FR-014**: Esta spec NO retira v1: sigue atendiendo consultas con normalidad después del `Sunset`. La retirada irá en otra petición con su propia spec.
- **FR-015**: Las respuestas de v2 y de `GET /health` NO DEBEN llevar estas cabeceras.

**Observabilidad y seguridad**

- **FR-016**: Las métricas de consultas DEBEN permitir separar el tráfico por versión de la API (v1 / v2), de modo que el panel «Consultas por versión de la API» muestre el tráfico de v2 diferenciado del de v1.
- **FR-017**: Cada endpoint de v2 DEBE dejar métricas y logs estructurados de su uso, sin datos personales; en las búsquedas solo se registra la longitud de `q` y el número de resultados, nunca su texto.
- **FR-018**: Los mensajes de error de v2 NO DEBEN exponer detalles internos (constitución, principio I).

### Key Entities

- **Producto (v2)**: artículo del catálogo con `id`, `nombre` y `precio`. Mismos datos que en v1; cambia la representación del precio.
- **Precio (v2)**: pareja de `importe` (texto decimal con 2 decimales) y `moneda` (código ISO 4217). La moneda es un atributo del producto en el catálogo.
- **Aviso de obsolescencia**: conjunto de las tres cabeceras (`Deprecation`, `Sunset`, `Link` de sucesión) que acompañan a toda respuesta de v1.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los productos devueltos por v2 tiene un precio con importe de exactamente 2 decimales y una moneda ISO 4217 válida.
- **SC-002**: Para cualquier `q` y cualquier identificador, v2 devuelve los mismos productos (o los mismos errores) que v1; la única diferencia es la forma del precio.
- **SC-003**: El 100 % de las respuestas de v1, incluidos los errores, lleva las tres cabeceras con los valores indicados.
- **SC-004**: Los cuerpos y códigos de estado de v1 son idénticos a los de antes del cambio en el 100 % de los casos probados.
- **SC-005**: Tras desplegar, el panel «Consultas por versión de la API» muestra el tráfico de v2 separado del de v1.
- **SC-006**: En ningún log ni métrica de v1 o v2 aparece el texto de `q`.

## Assumptions

- **Moneda única** (respuesta del responsable): hoy todo el catálogo está en euros y no hay precios en otras monedas. Varias monedas por producto quedan fuera de esta petición.
- **Sin redondeo** (respuesta del responsable): los precios del catálogo ya tienen exactamente 2 decimales (validado en el catálogo); el importe es ese mismo valor como texto.
- **Mismos campos y reglas** (respuesta del responsable): v2 solo cambia el precio; mismos errores, misma búsqueda y mismo límite de 200 caracteres.
- **Formato de las cabeceras** (respuesta del responsable): `Deprecation` como fecha estructurada (RFC 9745), `Sunset` como fecha HTTP (RFC 8594) y `Link` con `rel="successor-version"`. La petición original hablaba de «desde la fecha de despliegue»; prevalece la fecha fija indicada por el responsable (26-10-2026 00:00, hora de Madrid, `@1792969200`).
- **Fecha de Sunset** (respuesta del responsable): es correcta e intencionada, a pocos días de la fecha de esta spec. Es un entorno de staging de la POC, no hay clientes externos y el riesgo está aceptado.
- **Monedas sin 2 decimales** (JPY…): fuera de alcance. La regla de 2 decimales vale para EUR; si se añaden otras monedas, la regla irá por moneda en otra spec.
- **Panel de métricas**: «Consultas por versión de la API» se alimenta de las métricas de consultas de la aplicación. Esta spec exige que las métricas distingan la versión; la configuración del panel y las alertas viven fuera de este repositorio (despliegue) y no se modifican aquí.
- **Retirada de v1**: fuera de alcance; irá en otra petición. Tras el `Sunset` v1 sigue funcionando hasta entonces.
- **Anexo de la constitución**: esta spec cumple el aviso previo (`Deprecation`, `Sunset`) que exige antes de retirar una versión; la retirada requerirá una spec propia.
- **Fuera de alcance**: autenticación, paginación, filtros nuevos, conversión entre monedas, cambios en `GET /health` y cualquier cambio en el contenedor o el despliegue.
- El issue #6 se menciona como relacionado en el triage, pero nada indica que condicione esta spec.
