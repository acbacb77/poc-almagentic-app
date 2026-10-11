# Research: Buscar productos por nombre

- **Decisión**: normalizar con `unicodedata.normalize("NFD")`, quitar categoría `Mn` y `casefold()`.
  **Motivo**: biblioteca estándar, sin dependencias; ignora acentos y mayúsculas y unifica formas Unicode.
  **Alternativas**: `unidecode` (dependencia nueva, innecesaria); `str.lower()` (no cubre acentos).
- **Decisión**: filtrar en memoria con `in`.
  **Motivo**: catálogo de 5 a 10 productos; `in` es literal, así que no hay comodines ni inyección.
  **Alternativas**: expresiones regulares (requieren escapado, riesgo); índice (innecesario).
- **Decisión**: validar la longitud a mano tras `strip` y devolver 422 genérico.
  **Motivo**: `Query(max_length)` valida antes de quitar espacios y el 422 por defecto devuelve el valor recibido.
- **Decisión**: log y contador específicos de búsqueda sin el texto de `q`.
  **Motivo**: FR-011; el middleware existente no se modifica.
