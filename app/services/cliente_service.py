from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.schemas.cliente import ClienteAcesso


def identificar_cliente(db: Session, dados: ClienteAcesso) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.cpf == dados.cpf).first()
    if cliente:
        if cliente.telefone != dados.telefone:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Não foi possível validar os dados informados.")
        cliente.nome = dados.nome
    else:
        cliente = Cliente(**dados.model_dump())
        db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente
