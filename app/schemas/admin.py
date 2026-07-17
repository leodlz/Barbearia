from decimal import Decimal
from pydantic import BaseModel, Field


class ServicoAdminEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    descricao: str | None = None
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    duracao_minutos: int = Field(gt=0, le=480)


class BarbeiroAdminEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    descricao: str | None = None
    servico_ids: list[int] = []


class StatusEntrada(BaseModel):
    status: str
