from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.usuario_master import UsuarioMaster
from app.schemas.master import MasterLogin, MasterTrocaSenha
from app.services.cliente_service import gerar_hash, verificar_senha


def autenticar(db: Session, dados: MasterLogin) -> UsuarioMaster:
    usuario = db.query(UsuarioMaster).filter(func.lower(UsuarioMaster.usuario) == dados.usuario.lower()).first()
    if not usuario or not usuario.ativo or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário ou senha inválidos.")
    return usuario


def trocar_senha(db: Session, master: UsuarioMaster, dados: MasterTrocaSenha) -> None:
    if not verificar_senha(dados.senha_atual, master.senha_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Senha atual incorreta.")
    if dados.nova_senha != dados.confirmar_nova_senha:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "A confirmação da nova senha não confere.")
    if verificar_senha(dados.nova_senha, master.senha_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A nova senha deve ser diferente da senha atual.")

    master.senha_hash = gerar_hash(dados.nova_senha)
    db.commit()
