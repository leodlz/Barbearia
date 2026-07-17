from datetime import date, time

from pydantic import BaseModel


class DisponibilidadeSaida(BaseModel):
    barbeiro_id: int
    servico_id: int
    data: date
    duracao_minutos: int
    horarios: list[time]
