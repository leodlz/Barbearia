from datetime import date, time
from enum import Enum

from pydantic import BaseModel, ConfigDict


class StatusAgendamento(str, Enum):
    AGENDADO = "agendado"
    CANCELADO = "cancelado"
    CONCLUIDO = "concluido"
    FALTOU = "faltou"


class AgendamentoEntrada(BaseModel):
    cliente: str
    barbeiro: str
    data: date
    horario: time


class AgendamentoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente: str
    barbeiro: str
    data: date
    horario: time
    status: StatusAgendamento

