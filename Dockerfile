# Imagen de la API (tarea 9). La construye y la firma poc-almagentic-core/reusable-supply-chain.yml.
# Las imágenes base van fijadas por digest; el CI falla si alguna no lo está.
# El agente no puede modificar este fichero (check_pr_files.py, escaneo governance).

FROM ghcr.io/astral-sh/uv:0.11.32 AS uv

FROM python:3.12-slim-bookworm AS build
COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
# Solo las dependencias de producción, exactamente las de uv.lock.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src

FROM python:3.12-slim-bookworm
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/src /app/src
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
