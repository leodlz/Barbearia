from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.agendamento import Agendamento
from app.schemas.agendamento import AgendamentoEntrada, AgendamentoSaida


router = APIRouter()

@router.get("/agendamentos", response_model=list[AgendamentoSaida])
def listar_agendamentos(
    db: Session = Depends(get_db),
):
    agendamentos = db.query(Agendamento).all()
    return agendamentos

@router.post("/agendamentos", response_model=AgendamentoSaida)
def criar_agendamento(
    agendamento: AgendamentoEntrada,
    db: Session = Depends(get_db),
):
    conflito = db.query(Agendamento).filter(
        Agendamento.barbeiro == agendamento.barbeiro,
        Agendamento.data == agendamento.data,
        Agendamento.horario == agendamento.horario,
        Agendamento.status == "agendado",
    ).first()

    if conflito:
        raise HTTPException(
            status_code=409,
            detail="Este barbeiro já possui um agendamento nesse horário.",
        )

    novo_agendamento = Agendamento(
        cliente=agendamento.cliente,
        barbeiro=agendamento.barbeiro,
        data=agendamento.data,
        horario=agendamento.horario,
    )

    db.add(novo_agendamento)
    db.commit()
    db.refresh(novo_agendamento)

    return novo_agendamento
