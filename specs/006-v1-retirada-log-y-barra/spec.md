# Feature Specification: Cerrar los huecos de la retirada de v1 (log de acceso y /api/v1 sin barra)

**Feature Branch**: `spec/44-v1-retirada-log-y-barra` (spec) → `fix/44-v1-retirada-log-y-barra` (implementación)

**Created**: 2026-10-25

**Status**: Draft

**Issue**: #44

**Input**: User description: "La v1 retirada no debe registrar la ruta recibida. Dos huecos que quedaron de la retirada de v1 (spec 005, app#42): (1) el log de acceso de uvicorn registra la ruta completa recibida bajo /api/v1/…, que puede contener datos del cliente (va contra FR-013 y SC-006 de la spec 005); debe registrarse la ruta sin lo que sigue a /api/v1/, igual que ya se hace con la query string. (2) GET /api/v1 sin barra final puede responder 307 en lugar de 410; debe dar el mismo 410 con Link, Deprecation y Sunset." Completado con las respuestas del responsable en el issue #44: la ruta se registra con el marcador fijo `/api/v1/[retirada]`; el 410 de `/api/v1` sin barra se aplica a todos los métodos (HEAD sin cuerpo); solo se toca el log de acceso de uvicorn (métricas y logs propios de la app no se modifican, pero un test comprueba que siguen sin la ruta); los logs ya escritos quedan fuera de alcance; el cambio no es incompatible.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El log de acceso no guarda lo que el cliente envió a v1 (Priority: P1)

Quien opera el servicio revisa el log de acceso y ve que llegó tráfico a v1 (con su método y código), pero no encuentra en él ningún dato que el cliente haya puesto en la ruta ni en la query string.

**Why this priority**: Es un incumplimiento de privacidad de la spec 005 (FR-013, SC-006) y de la constitución (principio I): hoy la ruta completa, que puede contener datos del cliente, queda guardada en el log.

**Independent Test**: Se hacen llamadas a `/api/v1/productos/valor-secreto-123?q=dato-privado` y a una ruta inexistente como `/api/v1/otra-cosa/xyz`, y se comprueba que el log de acceso contiene `/api/v1/[retirada]` y no contiene ni `valor-secreto-123`, ni `otra-cosa`, ni `xyz`, ni `dato-privado`.

**Acceptance Scenarios**:

1. **Given** una petición a `/api/v1/productos/{id}` con un `id` reconocible, **When** se escribe el log de acceso, **Then** la ruta registrada es exactamente `/api/v1/[retirada]` y el log no contiene el `id`.
2. **Given** una petición a cualquier ruta bajo `/api/v1/` (existente, inexistente o con subrutas), **When** se escribe el log de acceso, **Then** la ruta registrada es `/api/v1/[retirada]` y no aparece nada de lo que seguía a `/api/v1/`.
3. **Given** una petición a v1 con query string, **When** se escribe el log de acceso, **Then** la query string tampoco aparece (se mantiene el comportamiento actual).
4. **Given** una petición a v1, **When** se escribe el log de acceso, **Then** siguen visibles el método, el código de estado (410) y el marcador, de modo que se ve que llegó tráfico a v1.
5. **Given** una petición a `/api/v1` sin barra final (con o sin query string), **When** se escribe el log de acceso, **Then** se registra igualmente con el marcador `/api/v1/[retirada]`.

---

### User Story 2 - /api/v1 sin barra final responde el mismo 410 (Priority: P1)

Un cliente rezagado que llama a `/api/v1` (sin barra final) recibe la misma respuesta de retirada que en el resto de v1, en lugar de una redirección 307.

**Why this priority**: Es el segundo hueco de la retirada: una redirección hace que una ruta de v1 siga sin responder 410 y no cumple FR-001 y FR-003 de la spec 005 en el límite del prefijo.

**Independent Test**: Se llama a `/api/v1` sin barra con GET, POST, PUT, PATCH, DELETE, HEAD y OPTIONS y se comprueba 410 en todos, con `Link`, `Deprecation` y `Sunset`, y sin cabecera `Location`.

**Acceptance Scenarios**:

1. **Given** la API desplegada, **When** se consulta `GET /api/v1`, **Then** la respuesta es 410 (no 307) con cuerpo `{"detail": "..."}` de mensaje genérico, igual que en el resto de rutas de v1.
2. **Given** la respuesta 410 de `/api/v1`, **When** se inspeccionan sus cabeceras, **Then** lleva `Deprecation: @1792969200`, `Sunset: Wed, 28 Oct 2026 23:00:00 GMT` y `Link: </api/v2>; rel="successor-version"`, con los mismos valores y formato que las demás rutas de v1 (spec 005, FR-005 a FR-007), además de `Cache-Control: no-store`.
3. **Given** cualquier método HTTP (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS), **When** se llama a `/api/v1` sin barra, **Then** la respuesta es el mismo 410 con las mismas cabeceras; en HEAD, sin cuerpo.
4. **Given** una llamada a `/api/v1` sin barra, **When** se responde, **Then** no hay cabecera `Location` ni redirección, y el cuerpo no repite texto recibido.
5. **Given** llamadas a `/api/v1` sin barra, **When** se leen las métricas de consultas, **Then** se contabilizan como versión v1 con código 410, sin crear series nuevas por valores recibidos (spec 005, FR-011 y FR-012).

---

### User Story 3 - Nada más cambia: v2, /health y el resto de rutas (Priority: P1)

Los clientes de v2 y los sistemas que vigilan `/health` no notan ningún cambio, y las rutas de v2 siguen registrándose en el log de acceso como hasta ahora.

**Why this priority**: El cambio debe limitarse al prefijo `/api/v1`; tocar el log o el enrutado de forma global rompería lo que sí está vigente.

**Independent Test**: Se llama a `/api/v2/productos`, `/api/v2/productos/{id}`, `/health` y a una ruta v2 con y sin barra final, y se comprueba que el log de acceso las registra con su ruta de siempre y que el comportamiento de enrutado no varía.

**Acceptance Scenarios**:

1. **Given** una petición a una ruta de v2 o a `/health`, **When** se escribe el log de acceso, **Then** se registra exactamente como antes de este cambio (misma ruta, sin marcador `[retirada]`).
2. **Given** una ruta de v2 con o sin barra final, **When** se consulta, **Then** el comportamiento de redirección o respuesta es el mismo que antes de este cambio; el 410 sin barra se aplica solo al prefijo `/api/v1`.
3. **Given** las respuestas de v2 y de `/health`, **When** se comparan con las anteriores al cambio, **Then** son idénticas en código, cuerpo y cabeceras.
4. **Given** una ruta de prefijo parecido (`/api/v10`, `/api/v1x`), **When** se consulta o se registra, **Then** se comporta como hasta ahora, sin 410 ni marcador.

---

### User Story 4 - Las métricas y los logs propios de la app siguen sin la ruta recibida (Priority: P2)

Quien audita la privacidad puede comprobar con un test que ni las métricas ni los logs propios de la aplicación contienen la ruta recibida bajo v1.

**Why this priority**: No requiere cambiar nada (ya cumplen), pero deja comprobada de extremo a extremo la garantía de SC-006 de la spec 005 y evita regresiones.

**Independent Test**: Tras llamar a rutas v1 con valores reconocibles en ruta y query, se leen las métricas y los logs propios de la app y se comprueba que ningún valor reconocible aparece.

**Acceptance Scenarios**:

1. **Given** llamadas a rutas v1 con valores reconocibles en ruta y query string, **When** se leen las métricas, **Then** esos valores no aparecen y las llamadas se agrupan bajo la versión v1 con código 410.
2. **Given** las mismas llamadas, **When** se revisan los logs propios de la aplicación, **Then** esos valores no aparecen.

---

### Edge Cases

- **Subrutas, barra final y caracteres especiales** (`/api/v1/productos/a/b`, `/api/v1/productos/`, `/api/v1/%2e%2e/x`): se registran siempre con el mismo marcador; nada de lo recibido pasa al log.
- **Prefijo**: se aplica la misma regla de prefijo que el 410 de la spec 005; lo que esa spec trata como v1 se registra con el marcador.
- **Prefijos parecidos** (`/api/v10/…`, `/api/v1x`): no son v1; ni 410 ni marcador.
- **Query string en `/api/v1` sin barra**: no aparece en el log; el `Link` sigue la misma regla que el resto de v1 (spec 005, FR-007).
- **Logs ya escritos**: los registros anteriores a este cambio conservan las rutas ya guardadas; limpiarlos está fuera de alcance.

## Requirements *(mandatory)*

### Functional Requirements

**Log de acceso**

- **FR-001**: El log de acceso DEBE registrar toda petición cuya ruta esté bajo `/api/v1/`, o sea exactamente `/api/v1`, con la ruta fija `/api/v1/[retirada]`, sin ninguna parte de lo que siga a `/api/v1/` en la petición recibida.
- **FR-002**: El log de acceso NO DEBE contener la query string de las peticiones a v1 (se mantiene el comportamiento actual).
- **FR-003**: Las entradas de v1 en el log de acceso DEBEN conservar el resto de campos que ya tienen (método, código de estado, etc.), de modo que siga viéndose que llegó tráfico a v1.
- **FR-004**: La sustitución por el marcador se DEBE limitar al prefijo `/api/v1`. Las rutas de v2, `/health`, prefijos parecidos (`/api/v10/…`) y cualquier otra ruta DEBEN registrarse exactamente igual que antes de este cambio.
- **FR-005**: Ningún valor recibido bajo `/api/v1/` (segmentos de ruta, `id`, `q`) DEBE aparecer en el log de acceso, ni tal cual ni transformado, aunque la petición sea inválida, malformada o apunte a una ruta inexistente.

**`/api/v1` sin barra final**

- **FR-006**: `/api/v1` (sin barra final), con cualquier método HTTP (GET, POST, PUT, PATCH, DELETE, HEAD y OPTIONS), DEBE responder 410 Gone con el mismo cuerpo genérico y las mismas cabeceras (`Deprecation`, `Sunset`, `Link` de sucesión, `Cache-Control: no-store`) que el resto de rutas de v1 (spec 005, FR-001 a FR-008). En HEAD no hay cuerpo.
- **FR-007**: `/api/v1` sin barra NO DEBE responder con una redirección ni con cabecera `Location`, ni con ningún código distinto de 410 (ni 307, ni 404, ni 405, ni 422).
- **FR-008**: El `Link` de la respuesta de `/api/v1` DEBE seguir la regla de la spec 005 (la ruta recibida con `v1` sustituido por `v2`, conservando `q` codificado si lo hay): `/api/v1` → `/api/v2`.
- **FR-009**: El comportamiento de redirección o enrutado de las rutas que no empiezan por `/api/v1` (en particular v2 y `/health`) NO DEBE cambiar; el 410 sin barra se resuelve solo para ese prefijo.
- **FR-010**: Las llamadas a `/api/v1` sin barra DEBEN contabilizarse en las métricas como versión v1 con código 410, sin series nuevas según lo recibido (spec 005, FR-011 y FR-012).

**Alcance y garantías**

- **FR-011**: Las métricas y los logs propios de la aplicación NO se modifican: ya no incluyen la ruta recibida y DEBEN seguir sin incluirla; un test lo comprueba.
- **FR-012**: v2 y `/health` NO DEBEN cambiar en comportamiento, códigos, cuerpos ni cabeceras. Este cambio no introduce nuevas versiones ni cambios incompatibles: los clientes de v1 ya recibían 410.

**Pruebas**

- **FR-013**: Cada criterio de aceptación de esta spec DEBE tener al menos un test automatizado, entre ellos: el log de acceso de v1 con el marcador y sin la ruta ni la query recibidas; el log de acceso de v2 y `/health` sin cambios; el 410 de `/api/v1` sin barra para todos los métodos con sus tres cabeceras y sin `Location`; el enrutado de v2 sin cambios; y métricas y logs propios sin la ruta recibida. Los tests existentes no se relajan ni se desactivan.

### Key Entities

- **Entrada del log de acceso**: línea que escribe el servidor por cada petición; para v1 contiene método, marcador `/api/v1/[retirada]` y código, y nada de lo recibido en la ruta ni en la query.
- **Respuesta de retirada**: la respuesta 410 de la spec 005 (mensaje genérico y cabeceras `Deprecation`, `Sunset`, `Link`), ahora también para `/api/v1` sin barra.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 0 % de las entradas del log de acceso de v1 contiene texto de la ruta recibida bajo `/api/v1/` ni de la query string; el 100 % muestra `/api/v1/[retirada]`.
- **SC-002**: El 100 % de las llamadas a `/api/v1` sin barra, con cualquiera de los siete métodos, devuelve 410 con `Link`, `Deprecation` y `Sunset`, y el 0 % devuelve una redirección.
- **SC-003**: Las entradas del log de acceso de v2, `/health` y rutas de prefijo parecido son idénticas a las anteriores al cambio en el 100 % de los casos probados.
- **SC-004**: El comportamiento de v2 y `/health` (respuestas y redirecciones) es idéntico al anterior en el 100 % de los casos probados.
- **SC-005**: Ningún valor reconocible enviado a v1 en la ruta o la query aparece en el log de acceso, las métricas ni los logs propios de la aplicación en los tests de verificación.

## Assumptions

- **Marcador** (respuesta del responsable): la ruta se registra como `/api/v1/[retirada]`, fija, para ver que llegó tráfico a v1 sin guardar nada de lo enviado.
- **`/api/v1` sin barra en el log**: al no seguirle nada a `/api/v1/`, se registra igualmente con el mismo marcador para tener una única forma de ver el tráfico de v1.
- **Métodos** (respuesta del responsable): los siete métodos dan el mismo 410 en `/api/v1` sin barra; HEAD sin cuerpo.
- **Otros registros** (respuesta del responsable): solo se cambia el log de acceso de uvicorn. Las métricas ya usan la plantilla de la ruta y los logs propios no registran la ruta recibida; no se tocan, solo se verifican con tests. Registros de infraestructura externa a esta aplicación (proxy, balanceador) quedan fuera de este repositorio.
- **Logs anteriores** (respuesta del responsable): los datos ya escritos en logs previos quedan fuera de alcance.
- **Tipo de cambio** (respuesta del responsable): es una corrección de la retirada de la spec 005, no un cambio incompatible; no crea `/api/v2` nuevo ni altera contratos publicados. Cumple FR-013 y SC-006 de esa spec y completa su FR-001 y FR-003.
- **Orden de entrega**: asume la spec 005 implementada y desplegada.
- **Fuera de alcance**: cambios en v2 o `/health`, cambios en el enrutado de otras rutas, borrado o anonimización de logs ya escritos, cambios en el contenedor (`Dockerfile`, `.dockerignore`) o en el despliegue, y configuración de paneles y alertas.
