from pydantic import BaseModel, ConfigDict, Field


class MasterLogin(BaseModel):
    usuario: str = Field(min_length=2, max_length=50)
    senha: str = Field(min_length=1, max_length=128)


class MasterTrocaSenha(BaseModel):
    senha_atual: str = Field(min_length=1, max_length=128)
    nova_senha: str = Field(min_length=8, max_length=128)
    confirmar_nova_senha: str = Field(min_length=8, max_length=128)


class MasterSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    usuario: str
    papel: str
