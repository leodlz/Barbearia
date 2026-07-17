from datetime import date, datetime, time

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.agendamento import Agendamento
from app.schemas.agendamento import AgendamentoEntrada, StatusAgendamento


def listar_agendamentos(db: Session) -> list[Agendamento]:
    return db.query(Agendamento).all()


def obter_agendamento(db: Session, agendamento_id: int) -> Agendamento:
    agendamento = db.get(Agendamento, agendamento_id)
    if agendamento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado.",
        )
    return agendamento


def criar_agendamento(
    db: Session,
    dados: AgendamentoEntrada,
) -> Agendamento:
    _validar_horario_futuro(dados.data, dados.horario)
    _validar_conflito(db, dados)

    agendamento = Agendamento(
        cliente=dados.cliente,
        barbeiro=dados.barbeiro,
        data=dados.data,
        horario=dados.horario,
    )
    db.add(agendamento)
    _salvar(db, agendamento)
    return agendamento


def cancelar_agendamento(db: Session, agendamento_id: int) -> Agendamento:
    agendamento = obter_agendamento(db, agendamento_id)
    _validar_status_agendado(agendamento, "cancelado")
    _validar_horario_futuro(agendamento.data, agendamento.horario)

    agendamento.status = StatusAgendamento.CANCELADO.value
    _salvar(db, agendamento)
    return agendamento


def concluir_agendamento(db: Session, agendamento_id: int) -> Agendamento:
    agendamento = obter_agendamento(db, agendamento_id)
    _validar_status_agendado(agendamento, "concluído")
    _validar_horario_decorrido(agendamento)

    agendamento.status = StatusAgendamento.CONCLUIDO.value
    _salvar(db, agendamento)
    return agendamento


def registrar_falta(db: Session, agendamento_id: int) -> Agendamento:
    agendamento = obter_agendamento(db, agendamento_id)
    _validar_status_agendado(agendamento, "marcado como falta")
    _validar_horario_decorrido(agendamento)

    agendamento.status = StatusAgendamento.FALTOU.value
    _salvar(db, agendamento)
    return agendamento


def _validar_conflito(db: Session, dados: AgendamentoEntrada) -> None:
    conflito = db.query(Agendamento).filter(
        Agendamento.barbeiro == dados.barbeiro,
        Agendamento.data == dados.data,
        Agendamento.horario == dados.horario,
        Agendamento.status == StatusAgendamento.AGENDADO.value,
    ).first()

    if conflito:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este barbeiro já possui um agendamento nesse horário.",
        )


def _validar_horario_futuro(data: date, horario: time) -> None:
    if datetime.combine(data, horario) <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="O agendamento deve ser marcado para uma data e horário futuros.",
        )


def _validar_horario_decorrido(agendamento: Agendamento) -> None:
    if datetime.combine(agendamento.data, agendamento.horario) > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta ação só pode ser realizada após o horário do agendamento.",
        )


def _validar_status_agendado(
    agendamento: Agendamento,
    novo_estado: str,
) -> None:
    if agendamento.status != StatusAgendamento.AGENDADO.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Um agendamento com status '{agendamento.status}' não pode ser "
                f"{novo_estado}."
            ),
        )


def _salvar(db: Session, agendamento: Agendamento) -> None:
    try:
        db.commit()
        db.refresh(agendamento)
    except SQLAlchemyError as erro:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar o agendamento.",
        ) from erro
