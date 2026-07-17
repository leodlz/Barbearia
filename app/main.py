from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.agendamentos import router as agendamentos_router
from app.routes.barbeiros import router as barbeiros_router
from app.routes.disponibilidade import router as disponibilidade_router
from app.routes.servicos import router as servicos_router

app = FastAPI(title="Gerenciador de Barbearia")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(agendamentos_router)
app.include_router(barbeiros_router)
app.include_router(servicos_router)
app.include_router(disponibilidade_router)


@app.get("/")
def inicio() -> dict[str, str]:
    return {"mensagem": "API da barbearia funcionando"}


@app.get("/status")
def status() -> dict[str, str]:
    return {"status": "online"}


@app.get("/web", include_in_schema=False)
def interface_web() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
