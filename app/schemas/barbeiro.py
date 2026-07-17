from pydantic import BaseModel, ConfigDict, Field

from app.schemas.servico import ServicoSaida


class BarbeiroEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=2, max_length=100)
    ativo: bool = True


class BarbeiroSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    ativo: bool
    servicos: list[ServicoSaida] = Field(default_factory=list)
