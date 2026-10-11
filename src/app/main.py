from fastapi import FastAPI
from pydantic import BaseModel


class EstadoSalud(BaseModel):
    status: str


def create_app() -> FastAPI:
    app = FastAPI(title="poc-almagentic-app")

    @app.get("/health")
    def health() -> EstadoSalud:
        return EstadoSalud(status="ok")

    return app


app = create_app()
