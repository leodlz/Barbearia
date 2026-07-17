from pydantic import BaseModel
from datetime import date, time


class AgendamentoEntrada(BaseModel):

    cliente: str
    barbeiro: str
    data: date
    horario: time

