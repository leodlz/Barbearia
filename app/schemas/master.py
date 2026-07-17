from pydantic import BaseModel, ConfigDict, Field


class MasterLogin(BaseModel):
    usuario: str = Field(min_length=2, max_length=50)
    senha: str = Field(min_length=1, max_length=128)


class MasterSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    usuario: str
    papel: str
