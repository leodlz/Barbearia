from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.servico import Servico
from app.schemas.servico import ServicoEntrada


def listar_servicos(db: Session, somente_ativos: bool = False) -> list[Servico]:
    consulta = db.query(Servico)
    if somente_ativos:
        consulta = consulta.filter(Servico.ativo.is_(True))
    return consulta.order_by(Servico.nome).all()


def obter_servico(db: Session, servico_id: int) -> Servico:
    servico = db.get(Servico, servico_id)
    if servico is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Serviço não encontrado.",
        )
    return servico


def criar_servico(db: Session, dados: ServicoEntrada) -> Servico:
    existente = db.query(Servico).filter(Servico.nome == dados.nome).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um serviço com esse nome.",
        )

    servico = Servico(**dados.model_dump())
    db.add(servico)
    _salvar(db, servico)
    return servico


def _salvar(db: Session, servico: Servico) -> None:
    try:
        db.commit()
        db.refresh(servico)
    except SQLAlchemyError as erro:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar o serviço.",
        ) from erro
