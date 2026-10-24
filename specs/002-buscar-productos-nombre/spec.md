# Feature Specification: Buscar productos del catálogo por nombre

**Feature Branch**: `spec/18-buscar-productos-nombre` (spec) → `feat/18-buscar-productos-nombre` (implementación)

**Created**: 2026-10-11

**Status**: Draft

**Issue**: #18

**Input**: User description: "Poder buscar productos del catálogo por nombre. Por ejemplo, GET /api/v1/productos?q=taza devolvería solo los productos cuyo nombre contiene «taza»." Completado con los criterios del issue #18 y la propuesta de triage.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filtrar el listado por nombre (Priority: P1)

La tienda web envía un texto de búsqueda al listado de productos y recibe solo los productos cuyo nombre contiene ese texto, para encontrar un producto sin recorrer todo el catálogo.

**Why this priority**: Es el motivo de la petición. Con solo esta historia la tienda ya puede ofrecer búsqueda por nombre.

**Independent Test**: Se consulta `GET /api/v1/productos?q=taza` y se comprueba que todos los productos devueltos tienen «taza» en el nombre y que no falta ningún producto del catálogo que lo tenga.

**Acceptance Scenarios**:

1. **Given** un catálogo con el producto «Taza azul» y otros cuyo nombre no contiene «taza», **When** se consulta el listado con `q=taza`, **Then** se devuelven solo los productos cuyo nombre contiene «taza», incluido «Taza azul».
2. **Given** un producto cuyo nombre contiene el texto buscado en medio o al final, **When** se busca ese texto, **Then** el producto aparece (la coincidencia es por fragmento en cualquier posición del nombre).
3. **Given** productos que coinciden, **When** se devuelve el resultado, **Then** cada producto tiene la misma forma (identificador, nombre y precio) y los mismos valores que en el listado completo, y mantienen entre sí el orden del listado completo.

---

### User Story 2 - Buscar sin importar mayúsculas ni acentos (Priority: P1)

La tienda busca con el texto tal como lo escribe la persona usuaria, con o sin acentos y en mayúsculas o minúsculas, y encuentra el producto igualmente.

**Why this priority**: Es un criterio explícito del issue; sin él la búsqueda falla con la escritura habitual.

**Independent Test**: Con un producto «Cerámica» en el catálogo, se buscan `q=ceramica`, `q=CERÁMICA` y `q=cerámica` y se comprueba que en los tres casos aparece.

**Acceptance Scenarios**:

1. **Given** el producto «Cerámica», **When** se busca `q=ceramica`, **Then** el producto aparece.
2. **Given** el producto «Cerámica», **When** se busca `q=CERÁMICA`, **Then** el producto aparece.
3. **Given** un producto cuyo nombre se escribe sin acentos, **When** se busca con acentos, **Then** el producto también aparece.

---

### User Story 3 - Búsqueda sin resultados o sin búsqueda (Priority: P2)

Si ningún producto coincide, la tienda recibe una respuesta correcta con una lista vacía, no un error. Si no envía `q`, el listado se comporta exactamente como hoy.

**Why this priority**: Protege a la tienda actual (compatibilidad con v1) y define el caso límite de la búsqueda, pero el valor principal ya lo dan las historias 1 y 2.

**Independent Test**: Se consulta el listado sin `q` y se compara con el comportamiento previo; se consulta con un texto que no coincide con nada y se comprueba que la respuesta es 200 con lista vacía.

**Acceptance Scenarios**:

1. **Given** el catálogo completo, **When** se consulta el listado sin el parámetro `q`, **Then** la respuesta es idéntica a la actual: todos los productos, mismo contenido y mismo orden.
2. **Given** un texto que no está en el nombre de ningún producto, **When** se busca con ese texto, **Then** la respuesta es 200 con una lista vacía.

---

### Edge Cases

- **`q` vacío o solo espacios** (`q=`, `q=%20%20`): se trata como si no se hubiera enviado y se devuelve el catálogo completo (ver FR-008).
- **Espacios alrededor del texto** (`q=%20taza%20`): se ignoran los espacios al principio y al final.
- **Caracteres especiales en `q`** (`%`, `_`, `*`, comillas, barras, etc.): se tratan como texto literal, nunca como comodines ni como parte de una consulta; si no están en ningún nombre, el resultado es una lista vacía.
- **`q` repetido** (`?q=taza&q=vaso`): el resultado es predecible y no provoca error del servidor (ver Assumptions).
- **`q` demasiado largo**: se rechaza con un error de validación (ver FR-009).
- **Nombres con distinta forma Unicode** (letra con acento precompuesta o descompuesta): se consideran equivalentes al buscar.
- **Consulta por identificador** (`GET /api/v1/productos/{id}`): no cambia y no se ve afectada por esta feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El listado `GET /api/v1/productos` DEBE aceptar un parámetro de consulta opcional `q` con el texto a buscar en el nombre de los productos.
- **FR-002**: Cuando se envía `q` con texto, el listado DEBE devolver solo los productos cuyo nombre contiene ese texto en cualquier posición.
- **FR-003**: La comparación NO DEBE distinguir mayúsculas de minúsculas ni acentos, en ambos sentidos (texto buscado y nombre).
- **FR-004**: Cuando no se envía `q`, la respuesta DEBE ser idéntica a la actual (mismos productos, mismos campos, mismo orden y mismo código de estado).
- **FR-005**: Cuando ningún producto coincide, el sistema DEBE responder 200 con una lista vacía, nunca 404.
- **FR-006**: Cada producto devuelto DEBE tener la misma forma y los mismos valores que en el listado completo, y los resultados DEBEN conservar el orden del listado completo.
- **FR-007**: El texto de `q` DEBE tratarse siempre como texto literal: ningún carácter de `q` actúa como comodín ni como instrucción.
- **FR-008**: Un `q` vacío o formado solo por espacios DEBE tratarse como ausente.
- **FR-009**: El texto de `q` DEBE tener un máximo de 200 caracteres después de quitar los espacios del principio y del final; un valor más largo se rechaza con un error de validación del cliente (422), sin detalles internos.
- **FR-010**: El parámetro `q` es opcional y se añade a la versión publicada `/api/v1`; no DEBE cambiar de forma incompatible ninguna respuesta existente (anexo de la constitución).
- **FR-011**: La búsqueda DEBE dejar métricas y logs estructurados de su uso, sin datos personales; en particular, solo se registran la longitud de `q` y el número de resultados; el texto de `q` NO DEBE registrarse nunca, ni tal cual ni transformado, porque lo escribe la persona usuaria final (anexo de la constitución).
- **FR-012**: Los errores de validación de `q` DEBEN devolver un mensaje genérico, sin detalles internos (constitución, principio I).

### Key Entities

- **Producto**: el existente (identificador, nombre y precio). Esta feature no añade ni cambia atributos; solo su nombre se usa para buscar.
- **Búsqueda por nombre**: texto opcional que la tienda envía junto al listado para acotar los productos devueltos. No se guarda.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La tienda web encuentra cualquier producto escribiendo un fragmento de su nombre, sin recorrer el catálogo completo: el 100 % de los productos cuyo nombre contiene el texto buscado aparece en el resultado, y ningún otro.
- **SC-002**: Buscar sin distinguir mayúsculas ni acentos funciona en el 100 % de los casos probados («Cerámica» se encuentra con `ceramica`, `CERÁMICA` y `cerámica`).
- **SC-003**: El 100 % de las consultas al listado sin `q` devuelven exactamente lo mismo que antes de esta feature, de modo que la tienda actual no necesita ningún cambio.
- **SC-004**: El 100 % de las búsquedas sin coincidencias reciben una respuesta correcta con una lista vacía, sin errores.
- **SC-005**: La búsqueda no añade una espera perceptible: el resultado llega en menos de 1 segundo, igual que el listado actual.

## Assumptions

- **Tipo de coincidencia**: «contiene» se interpreta como coincidencia por fragmento en cualquier posición del nombre (no solo al principio ni palabra completa).
- **Acentos**: ignorar acentos significa tratar «á» y «a», «ñ» y «n», etc. como equivalentes. Se aplica solo al nombre; el identificador y el precio no se buscan.
- **Espacios**: se ignoran los espacios al principio y al final del texto buscado; los espacios interiores se mantienen como parte del texto.
- **`q` vacío**: por compatibilidad con v1 y por ser lo menos sorprendente para la tienda, se asume que `q` vacío o solo con espacios equivale a no enviarlo. Confirmado por el responsable (FR-008).
- **`q` repetido**: se usa un único valor de `q` y los demás se ignoran, sin error.
- **Longitud máxima**: se fija en 200 caracteres tras quitar espacios (ampliado desde 100 por la spec 003, issue #29). Confirmado por el responsable (FR-009).
- **Combinación con paginación y filtros**: hoy el listado no tiene paginación ni otros filtros (spec 001, FR-008), así que no hay nada con lo que combinarla. Si se añaden más adelante, deberán combinarse con `q` en su propia spec.
- **Relación con la spec 001**: la spec `001-catalogo-productos` (FR-008) dice que el listado se devuelve «sin paginación ni filtros». Esta feature lo modifica de forma compatible: sin `q` el listado sigue siendo el catálogo completo. Solo `q` deja de estar fuera de alcance; paginación y otros filtros siguen fuera.
- **Sin autenticación**: igual que el listado actual, la búsqueda es pública.
- **Fuera de alcance**: ordenar por relevancia, buscar por otros campos (precio, identificador), coincidencias aproximadas o con erratas, sinónimos, paginación, autocompletado y cambios en `GET /api/v1/productos/{id}`.
- **Rendimiento**: el catálogo es pequeño y fijo (5 a 10 productos, spec 001), por lo que no se exige índice ni infraestructura especial. Si el catálogo creciera mucho, habría que reevaluarlo.
