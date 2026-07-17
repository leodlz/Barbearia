import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.routes.agendamentos import router as agendamentos_router
from app.routes.admin_auth import router as admin_auth_router
from app.routes.admin import router as admin_router
from app.routes.barbeiros import router as barbeiros_router
from app.routes.clientes import router as clientes_router
from app.routes.disponibilidade import router as disponibilidade_router
from app.routes.servicos import router as servicos_router

app = FastAPI(title="Gerenciador de Barbearia")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "desenvolvimento-troque-em-producao"), max_age=3600, same_site="lax", https_only=os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(agendamentos_router)
app.include_router(barbeiros_router)
app.include_router(servicos_router)
app.include_router(disponibilidade_router)
app.include_router(clientes_router)
app.include_router(admin_auth_router)
app.include_router(admin_router)


@app.get("/")
def inicio() -> dict[str, str]:
    return {"mensagem": "API da barbearia funcionando"}


@app.get("/status")
def status() -> dict[str, str]:
    return {"status": "online"}


@app.get("/web", include_in_schema=False)
def interface_web() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
