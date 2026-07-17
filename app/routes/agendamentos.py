from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.agendamento import AgendamentoEntrada, AgendamentoSaida
from app.services import agendamento_service


router = APIRouter()

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
