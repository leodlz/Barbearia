from datetime import date, time
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.schemas.barbeiro import BarbeiroResumo
from app.schemas.servico import ServicoSaida


class StatusAgendamento(str, Enum):
    AGENDADO = "agendado"
    CANCELADO = "cancelado"
    CONCLUIDO = "concluido"
    FALTOU = "faltou"


class AgendamentoEntrada(BaseModel):
    cliente: str
    barbeiro_id: int
    servico_id: int
    data: date
    horario: time


class AgendamentoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente: str
    barbeiro_id: int
    servico_id: int
    data: date
    horario: time
    status: StatusAgendamento
    barbeiro: BarbeiroResumo
    servico: ServicoSaida

