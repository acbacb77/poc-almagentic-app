# Feature Specification: Ampliar el límite de longitud de la búsqueda de productos

**Feature Branch**: `spec/29-ampliar-limite-busqueda` (spec) → `feat/29-ampliar-limite-busqueda` (implementación)

**Created**: 2026-10-24

**Status**: Draft

**Retirada**: la API v1 que define esta spec está retirada por la [spec 005](../005-retirar-api-v1/spec.md) (todas las rutas `/api/v1/` responden 410). Se conserva como histórico y como fuente de las reglas que reutiliza v2.

**Issue**: #29

**Input**: User description: "En staging, el 100 % de las búsquedas de los últimos 5 minutos (`GET /api/v1/productos?q=…`) recibió 422 porque `q` supera los 100 caracteres (FR-009 de la spec 002). Decisión del responsable: subir el máximo de `q` de 100 a 200 caracteres, contados tras quitar los espacios del principio y del final; por encima de 200 se sigue devolviendo el 422 genérico; se mantiene FR-011 (en el log solo la longitud, nunca el texto)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Buscar con textos de hasta 200 caracteres (Priority: P1)

La tienda web envía a la búsqueda un texto de entre 101 y 200 caracteres y recibe el resultado normal de la búsqueda, en lugar de un error de validación.

**Why this priority**: Es el cambio pedido y lo que hace que la alerta `BusquedasRechazadas` deje de dispararse con el mismo tráfico.

**Independent Test**: Se consulta `GET /api/v1/productos?q=<texto de 120 caracteres>` y se comprueba que la respuesta es 200 (con la lista de coincidencias, vacía si nada coincide), no 422.

**Acceptance Scenarios**:

1. **Given** un texto de búsqueda de 120 caracteres, **When** se consulta el listado con ese `q`, **Then** la respuesta es 200 y aplica las mismas reglas de búsqueda de la spec 002 (coincidencia por fragmento, sin distinguir mayúsculas ni acentos).
2. **Given** un texto de exactamente 200 caracteres, **When** se consulta el listado, **Then** la respuesta es 200.
3. **Given** un texto de 100 caracteres o menos, **When** se consulta el listado, **Then** el comportamiento es idéntico al actual.

---

### User Story 2 - Seguir rechazando textos demasiado largos (Priority: P1)

Un texto de más de 200 caracteres sigue rechazándose con el mismo error de validación genérico, de modo que el límite protege a la búsqueda de entradas desproporcionadas.

**Why this priority**: El límite sigue existiendo; solo cambia su valor. Sin esta historia el cambio degradaría la protección.

**Independent Test**: Se consulta con un `q` de 201 caracteres y se comprueba que la respuesta es 422 con el mensaje genérico de siempre.

**Acceptance Scenarios**:

1. **Given** un texto de 201 caracteres, **When** se consulta el listado, **Then** la respuesta es 422 con el mismo mensaje genérico que hoy, sin detalles internos.
2. **Given** un texto de 201 caracteres de los cuales los primeros o los últimos son espacios, de modo que tras quitarlos quedan 200 o menos, **When** se consulta el listado, **Then** la respuesta es 200.
3. **Given** un texto que tras quitar los espacios de los extremos tiene 201 caracteres o más, **When** se consulta el listado, **Then** la respuesta es 422.

---

### User Story 3 - Privacidad intacta en los logs (Priority: P1)

Quien opera el servicio sigue viendo en los logs de búsqueda solo la longitud de `q` (y el número de resultados), nunca el texto, también para las longitudes nuevas.

**Why this priority**: Es una obligación de la constitución y del FR-011 de la spec 002; la longitud registrada es además lo que permitió diagnosticar este incidente.

**Independent Test**: Se hacen búsquedas con 150 y 200 caracteres y se comprueba que el log contiene la longitud pero ninguna parte del texto.

**Acceptance Scenarios**:

1. **Given** una búsqueda con un `q` de 150 caracteres, **When** se registra su uso, **Then** el log contiene la longitud (150) y no el texto, ni tal cual ni transformado.

---

### Edge Cases

- **Frontera exacta**: 200 caracteres se aceptan; 201 se rechazan (tras quitar espacios de los extremos).
- **Espacios**: los espacios del principio y del final no cuentan; los interiores sí.
- **Caracteres no ASCII**: la longitud se cuenta en caracteres, no en bytes (una «ñ» o una «á» cuenta como uno), igual que en la spec 002.
- **`q` vacío o solo espacios**: sigue tratándose como ausente (spec 002, FR-008), sin cambios.
- **Consultas de 101 a 200 caracteres sin coincidencias**: respuesta 200 con lista vacía, no error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El texto de `q` DEBE tener un máximo de **200 caracteres** después de quitar los espacios del principio y del final. Esta spec **sustituye** el valor de 100 de la spec 002, FR-009.
- **FR-002**: Un `q` de más de 200 caracteres (tras quitar espacios de los extremos) DEBE rechazarse con el mismo error de validación del cliente (422) y el mismo mensaje genérico que hoy, sin detalles internos (spec 002, FR-009 y FR-012).
- **FR-003**: Un `q` de entre 101 y 200 caracteres DEBE procesarse como cualquier otra búsqueda válida, con las reglas de la spec 002 (FR-002 a FR-008).
- **FR-004**: Para `q` de 100 caracteres o menos, o ausente, el comportamiento DEBE ser idéntico al actual.
- **FR-005**: La longitud se DEBE contar en caracteres (no en bytes) y después de quitar los espacios del principio y del final.
- **FR-006**: El registro y las métricas de la búsqueda DEBEN seguir recogiendo solo la longitud de `q` y el número de resultados; el texto de `q` NO DEBE registrarse nunca, ni tal cual ni transformado (spec 002, FR-011), tampoco en las búsquedas rechazadas.
- **FR-007**: Las métricas y la alerta de búsquedas rechazadas por validación DEBEN mantenerse con el mismo significado: una búsqueda de más de 200 caracteres sigue contando como rechazada.
- **FR-008**: El cambio es compatible con `/api/v1`: solo se aceptan entradas que antes se rechazaban, y ninguna respuesta existente cambia (anexo de la constitución). No se crea `/api/v2`.
- **FR-009**: La spec 002 DEBE reflejar el nuevo límite (FR-009, Assumptions «Longitud máxima» y los tests asociados), de modo que quede una única fuente de verdad sobre el máximo.

### Key Entities

- **Búsqueda por nombre**: texto opcional `q` que la tienda envía al listado. Solo cambia la longitud máxima admitida (de 100 a 200 caracteres); sigue sin guardarse.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las búsquedas cuyo texto tiene entre 101 y 200 caracteres (tras quitar espacios de los extremos) recibe una respuesta correcta (200), no un error de validación.
- **SC-002**: El 100 % de las búsquedas de más de 200 caracteres sigue recibiendo el error de validación genérico.
- **SC-003**: Las búsquedas de 100 caracteres o menos devuelven exactamente lo mismo que antes del cambio.
- **SC-004**: En ningún log ni métrica de la búsqueda aparece texto de `q`; solo su longitud.
- **SC-005**: Con el mismo tráfico que disparó el incidente (consultas de unos 120 caracteres), la alerta `BusquedasRechazadas` deja de dispararse en staging.

## Assumptions

- **Causa y alcance del incidente** (respuesta del responsable en el issue #29): la causa es un cliente de pruebas que envía 120 caracteres y solo afecta a staging. Producción no está afectada.
- **Decisión de producto**: el responsable ha decidido subir el límite a 200 en lugar de cambiar el cliente de pruebas. El valor es una decisión explícita, no un cálculo a partir de datos de uso.
- **Relación con la spec 002**: esta spec modifica solo el valor del límite de FR-009; el resto de la spec 002 sigue vigente. Para mantener una única fuente de verdad, el PR de implementación actualiza el FR-009 y la asunción «Longitud máxima» de la spec 002 (FR-009 de esta spec). Este PR de spec no modifica la spec 002 para no dejarla en contradicción con el código hasta que se implemente.
- **Sin otros cambios**: no se tocan la forma de la respuesta, la autenticación (la búsqueda sigue siendo pública), el orden ni los demás parámetros.
- **Rendimiento**: el catálogo es pequeño y fijo (spec 001); duplicar la longitud máxima del texto no tiene un coste apreciable. No se exige nada adicional.
- **Fuera de alcance**: corregir el cliente de pruebas de staging, cambiar la regla o el umbral de la alerta `BusquedasRechazadas`, y cualquier otro cambio en la búsqueda.
