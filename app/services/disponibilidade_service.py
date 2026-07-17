from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.agendamento import Agendamento
from app.schemas.agendamento import StatusAgendamento
from app.services.agendamento_service import validar_catalogo
from app.services.barbeiro_service import obter_barbeiro
from app.services.servico_service import obter_servico


ABERTURA = time(9)
INICIO_INTERVALO = time(12)
FIM_INTERVALO = time(13)
FECHAMENTO = time(18)
PASSO_MINUTOS = 30
DOMINGO = 6


def listar_horarios(
    db: Session,
    barbeiro_id: int,
    servico_id: int,
    data_escolhida: date,
) -> dict:
    barbeiro = obter_barbeiro(db, barbeiro_id)
    servico = obter_servico(db, servico_id)
    validar_catalogo(barbeiro, servico)

    if data_escolhida.weekday() == DOMINGO:
        horarios: list[time] = []
    else:
        horarios = _calcular_horarios(
            db,
            barbeiro_id,
            servico.duracao_minutos,
            data_escolhida,
        )

    return {
        "barbeiro_id": barbeiro_id,
        "servico_id": servico_id,
        "data": data_escolhida,
        "duracao_minutos": servico.duracao_minutos,
        "horarios": horarios,
    }


def _calcular_horarios(
    db: Session,
    barbeiro_id: int,
    duracao_minutos: int,
    data_escolhida: date,
) -> list[time]:
    inicio_expediente = datetime.combine(data_escolhida, ABERTURA)
    fim_expediente = datetime.combine(data_escolhida, FECHAMENTO)
    inicio_intervalo = datetime.combine(data_escolhida, INICIO_INTERVALO)
    fim_intervalo = datetime.combine(data_escolhida, FIM_INTERVALO)

    ocupados = db.query(Agendamento).filter(
        Agendamento.barbeiro_id == barbeiro_id,
        Agendamento.data == data_escolhida,
        Agendamento.status.in_([StatusAgendamento.AGENDADO.value, StatusAgendamento.CONFIRMADO.value]),
    ).all()

    horarios = []
    candidato = inicio_expediente
    agora = datetime.now()

    while candidato + timedelta(minutes=duracao_minutos) <= fim_expediente:
        fim_candidato = candidato + timedelta(minutes=duracao_minutos)
        sobrepoe_intervalo = (
            candidato < fim_intervalo and fim_candidato > inicio_intervalo
        )
        sobrepoe_agendamento = any(
            candidato < _fim_agendamento(agendamento)
            and fim_candidato > datetime.combine(
                agendamento.data,
                agendamento.horario,
            )
            for agendamento in ocupados
        )

        if candidato > agora and not sobrepoe_intervalo and not sobrepoe_agendamento:
            horarios.append(candidato.time())

        candidato += timedelta(minutes=PASSO_MINUTOS)

    return horarios


def _fim_agendamento(agendamento: Agendamento) -> datetime:
    inicio = datetime.combine(agendamento.data, agendamento.horario)
    return inicio + timedelta(minutes=agendamento.servico.duracao_minutos)
