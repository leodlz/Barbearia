from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.cliente import Cliente
from app.models.usuario_master import UsuarioMaster


def require_cliente(request: Request, db: Session = Depends(get_db)) -> Cliente:
    cliente_id = request.session.get("cliente_id")
    cliente = db.get(Cliente, cliente_id) if cliente_id else None
    if not cliente:
        if request.session.get("master_id"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta área é exclusiva para clientes.")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada. Entre novamente.")
    return cliente


def require_master(request: Request, db: Session = Depends(get_db)) -> UsuarioMaster:
    master_id = request.session.get("master_id")
    master = db.get(UsuarioMaster, master_id) if master_id else None
    if not master or not master.ativo:
        if request.session.get("cliente_id"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem permissão para acessar esta área.")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Autenticação administrativa necessária.")
    return master
