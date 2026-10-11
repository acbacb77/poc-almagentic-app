# Quickstart: búsqueda por nombre

```bash
uv run pytest -q tests/api/v1/test_busqueda.py
uv run uvicorn app.main:app --app-dir src
curl 'http://localhost:8000/api/v1/productos?q=ceramica'   # productos con «cerámica»
curl 'http://localhost:8000/api/v1/productos?q=zzz'        # 200 y []
curl 'http://localhost:8000/api/v1/productos'              # catálogo completo
```
