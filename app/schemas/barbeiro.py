from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

from app.schemas.servico import ServicoSaida


class BarbeiroEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=2, max_length=100)
    descricao: str | None = Field(default=None, max_length=500)
    ativo: bool = True


class BarbeiroResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    ativo: bool
    descricao: str | None
    criado_em: datetime
    atualizado_em: datetime


class BarbeiroSaida(BarbeiroResumo):
    servicos: list[ServicoSaida] = Field(default_factory=list)
