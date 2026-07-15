from pydantic import BaseModel
from datetime import date, time


class AgendamentoEntrada(BaseModel):

    client: str
    barbeiro: str
    data: date
    horario: time

