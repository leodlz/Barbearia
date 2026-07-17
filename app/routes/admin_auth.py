from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_master
from app.models.usuario_master import UsuarioMaster
from app.schemas.master import MasterLogin, MasterSaida, MasterTrocaSenha
from app.services import master_service

router = APIRouter(tags=["Admin"])
STATIC = Path(__file__).parents[1] / "static"

@router.get("/admin/login", include_in_schema=False)
def pagina_login(): return FileResponse(STATIC / "admin-login.html")

@router.post("/api/admin/login", response_model=MasterSaida)
def login(dados: MasterLogin, request: Request, db: Session = Depends(get_db)):
    master = master_service.autenticar(db, dados)
    request.session.clear(); request.session["master_id"] = master.id
    return master

@router.post("/api/admin/logout", status_code=204)
def logout(request: Request): request.session.clear()

@router.get("/api/admin/me", response_model=MasterSaida)
def me(master: UsuarioMaster = Depends(require_master)): return master

@router.put("/api/admin/senha", status_code=204)
def trocar_senha(dados: MasterTrocaSenha, master: UsuarioMaster = Depends(require_master), db: Session = Depends(get_db)):
    master_service.trocar_senha(db, master, dados)

@router.get("/admin", include_in_schema=False)
def dashboard(_: UsuarioMaster = Depends(require_master)): return FileResponse(STATIC / "admin.html")
