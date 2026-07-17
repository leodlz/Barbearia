import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.agendamento import AgendamentoEntrada, AgendamentoSaida
from app.services import agendamento_service


def validar_admin(x_admin_key: str | None = Header(default=None)) -> None:
    chave = os.getenv("ADMIN_API_KEY")
    if not chave or not x_admin_key or not secrets.compare_digest(chave, x_admin_key):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso administrativo não autorizado.")


router = APIRouter(tags=["Agendamentos"], dependencies=[Depends(validar_admin)])

@router.get("/agendamentos", response_model=list[AgendamentoSaida])
def listar_agendamentos(
    db: Session = Depends(get_db),
):
    return agendamento_service.listar_agendamentos(db)


@router.get("/agendamentos/{agendamento_id}", response_model=AgendamentoSaida)
def buscar_agendamento(
    agendamento_id: int,
    db: Session = Depends(get_db),
):
    return agendamento_service.obter_agendamento(db, agendamento_id)


@router.post(
    "/agendamentos",
    response_model=AgendamentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def criar_agendamento(
    agendamento: AgendamentoEntrada,
    db: Session = Depends(get_db),
):
    return agendamento_service.criar_agendamento(db, agendamento)


@router.patch(
    "/agendamentos/{agendamento_id}/cancelar",
    response_model=AgendamentoSaida,
)
def cancelar_agendamento(
    agendamento_id: int,
    db: Session = Depends(get_db),
):
    return agendamento_service.cancelar_agendamento(db, agendamento_id)


@router.patch(
    "/agendamentos/{agendamento_id}/concluir",
    response_model=AgendamentoSaida,
)
def concluir_agendamento(
    agendamento_id: int,
    db: Session = Depends(get_db),
):
    return agendamento_service.concluir_agendamento(db, agendamento_id)


@router.patch(
    "/agendamentos/{agendamento_id}/falta",
    response_model=AgendamentoSaida,
)
def registrar_falta(
    agendamento_id: int,
    db: Session = Depends(get_db),
):
    return agendamento_service.registrar_falta(db, agendamento_id)
