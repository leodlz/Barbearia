from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.usuario_master import UsuarioMaster
from app.schemas.master import MasterLogin
from app.services.cliente_service import verificar_senha


def autenticar(db: Session, dados: MasterLogin) -> UsuarioMaster:
    usuario = db.query(UsuarioMaster).filter(func.lower(UsuarioMaster.usuario) == dados.usuario.lower()).first()
    if not usuario or not usuario.ativo or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário ou senha inválidos.")
    return usuario
