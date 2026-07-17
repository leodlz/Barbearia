import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalizar_cpf(valor: str) -> str:
    if re.search(r"[A-Za-z]", valor):
        raise ValueError("CPF inválido. Confira os números informados.")
    cpf = re.sub(r"\D", "", valor)
    if len(cpf) != 11 or len(set(cpf)) == 1:
        raise ValueError("CPF inválido. Confira os números informados.")
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[tamanho]):
            raise ValueError("CPF inválido. Confira os números informados.")
    return cpf


def normalizar_telefone(valor: str) -> str:
    if re.search(r"[A-Za-z]", valor):
        raise ValueError("Telefone inválido. Confira o DDD e o número.")
    telefone = re.sub(r"\D", "", valor)
    if len(telefone) not in (10, 11):
        raise ValueError("Telefone inválido. Confira o DDD e o número.")
    return telefone


class ClienteAcesso(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nome: str = Field(min_length=3, max_length=100)
    telefone: str
    cpf: str

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: str) -> str:
        return normalizar_telefone(valor)

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        return normalizar_cpf(valor)


class ClienteSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    telefone: str
