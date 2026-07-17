from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServicoEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=2, max_length=100)
    descricao: str | None = Field(default=None, max_length=500)
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    duracao_minutos: int = Field(gt=0, le=480)
    ativo: bool = True


class ServicoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    preco: Decimal
    duracao_minutos: int
    ativo: bool
