from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.agendamento import Agendamento
from app.models.barbeiro import Barbeiro
from app.models.servico import Servico
from app.schemas.agendamento import AgendamentoEntrada, StatusAgendamento
from app.services.barbeiro_service import obter_barbeiro
from app.services.servico_service import obter_servico
from app.services.relogio import agora_local


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
    cliente_id: int | None = None,
) -> Agendamento:
    _validar_horario_futuro(dados.data, dados.horario)
    barbeiro = obter_barbeiro(db, dados.barbeiro_id)
    servico = obter_servico(db, dados.servico_id)
    validar_catalogo(barbeiro, servico)
    _validar_conflito(db, dados, servico)

    agendamento = Agendamento(
        cliente=dados.cliente,
        barbeiro_id=dados.barbeiro_id,
        servico_id=dados.servico_id,
        data=dados.data,
        horario=dados.horario,
        cliente_id=cliente_id,
        preco_no_agendamento=servico.preco,
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


def alterar_status(db: Session, agendamento_id: int, novo_status: str) -> Agendamento:
    agendamento = obter_agendamento(db, agendamento_id)
    permitidos = {"agendado": {"confirmado", "cancelado", "concluido", "faltou"}, "confirmado": {"cancelado", "concluido", "faltou"}}
    if novo_status not in permitidos.get(agendamento.status, set()):
        raise HTTPException(status.HTTP_409_CONFLICT, "Transição de status inválida.")
    if novo_status == "cancelado": return cancelar_agendamento(db, agendamento_id)
    if novo_status == "concluido": return concluir_agendamento(db, agendamento_id)
    if novo_status == "faltou": return registrar_falta(db, agendamento_id)
    agendamento.status = novo_status; _salvar(db, agendamento); return agendamento


def _validar_conflito(
    db: Session,
    dados: AgendamentoEntrada,
    servico: Servico,
) -> None:
    agendamentos_ativos = db.query(Agendamento).filter(
        Agendamento.barbeiro_id == dados.barbeiro_id,
        Agendamento.data == dados.data,
        Agendamento.status.in_([StatusAgendamento.AGENDADO.value, StatusAgendamento.CONFIRMADO.value]),
    ).all()

    novo_inicio = datetime.combine(dados.data, dados.horario)
    novo_fim = novo_inicio + timedelta(minutes=servico.duracao_minutos)

    conflito = any(
        novo_inicio
        < datetime.combine(existente.data, existente.horario)
        + timedelta(minutes=existente.servico.duracao_minutos)
        and novo_fim > datetime.combine(existente.data, existente.horario)
        for existente in agendamentos_ativos
    )

    if conflito:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este horário acabou de ser reservado. Escolha outro horário.",
        )


def validar_catalogo(barbeiro: Barbeiro, servico: Servico) -> None:
    if not barbeiro.ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O barbeiro informado está inativo.",
        )
    if not servico.ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O serviço informado está inativo.",
        )
    if servico not in barbeiro.servicos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O barbeiro informado não realiza este serviço.",
        )


def _validar_horario_futuro(data: date, horario: time) -> None:
    if datetime.combine(data, horario) <= agora_local():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="O agendamento deve ser marcado para uma data e horário futuros.",
        )


def _validar_horario_decorrido(agendamento: Agendamento) -> None:
    if datetime.combine(agendamento.data, agendamento.horario) > agora_local():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta ação só pode ser realizada após o horário do agendamento.",
        )


def _validar_status_agendado(
    agendamento: Agendamento,
    novo_estado: str,
) -> None:
    if agendamento.status not in (StatusAgendamento.AGENDADO.value, StatusAgendamento.CONFIRMADO.value):
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
