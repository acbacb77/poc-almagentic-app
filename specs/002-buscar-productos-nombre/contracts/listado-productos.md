# Contrato: GET /api/v1/productos

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `q` | texto, máx. 100 caracteres tras quitar espacios | No | Fragmento del nombre; sin mayúsculas ni acentos. Vacío = ausente. |

- `200`: `list[Producto]` (`id`, `nombre`, `precio`) en el orden del catálogo; lista vacía si no hay coincidencias.
- `422`: `q` de más de 100 caracteres; cuerpo `{"detail": "Parámetro q no válido"}`.
- Todas las respuestas llevan `Cache-Control: no-store`.
