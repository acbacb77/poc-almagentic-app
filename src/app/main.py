from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from app.catalogo import RUTA_CATALOGO, cargar_catalogo


class EstadoSalud(BaseModel):
    status: str


def create_app(ruta_catalogo: Path = RUTA_CATALOGO) -> FastAPI:
    app = FastAPI(title="poc-almagentic-app")
    # Un catálogo mal formado impide arrancar: nunca llega a servirse (FR-010).
    app.state.catalogo = cargar_catalogo(ruta_catalogo)

    @app.get("/health")
    def health() -> EstadoSalud:
        return EstadoSalud(status="ok")

    return app


app = create_app()
