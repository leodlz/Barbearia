from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.barbeiro import Barbeiro
from app.schemas.barbeiro import BarbeiroEntrada
from app.services.servico_service import obter_servico


def listar_barbeiros(db: Session, somente_ativos: bool = False) -> list[Barbeiro]:
    consulta = db.query(Barbeiro)
    if somente_ativos:
        consulta = consulta.filter(Barbeiro.ativo.is_(True))
    return consulta.order_by(Barbeiro.nome).all()


def obter_barbeiro(db: Session, barbeiro_id: int) -> Barbeiro:
    barbeiro = db.get(Barbeiro, barbeiro_id)
    if barbeiro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barbeiro não encontrado.",
        )
    return barbeiro


def criar_barbeiro(db: Session, dados: BarbeiroEntrada) -> Barbeiro:
    existente = db.query(Barbeiro).filter(Barbeiro.nome == dados.nome).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um barbeiro com esse nome.",
        )

    barbeiro = Barbeiro(**dados.model_dump())
    db.add(barbeiro)
    _salvar(db, barbeiro)
    return barbeiro


def associar_servico(
    db: Session,
    barbeiro_id: int,
    servico_id: int,
) -> Barbeiro:
    barbeiro = obter_barbeiro(db, barbeiro_id)
    servico = obter_servico(db, servico_id)
    if servico in barbeiro.servicos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este barbeiro já realiza o serviço informado.",
        )

    barbeiro.servicos.append(servico)
    _salvar(db, barbeiro)
    return barbeiro


def remover_servico(db: Session, barbeiro_id: int, servico_id: int) -> None:
    barbeiro = obter_barbeiro(db, barbeiro_id)
    servico = obter_servico(db, servico_id)
    if servico not in barbeiro.servicos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O barbeiro não realiza o serviço informado.",
        )

    barbeiro.servicos.remove(servico)
    try:
        db.commit()
    except SQLAlchemyError as erro:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível remover o serviço do barbeiro.",
        ) from erro


def _salvar(db: Session, barbeiro: Barbeiro) -> None:
    try:
        db.commit()
        db.refresh(barbeiro)
    except SQLAlchemyError as erro:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar o barbeiro.",
        ) from erro
