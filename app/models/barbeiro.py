from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base
from app.models.associacoes import barbeiros_servicos


class Barbeiro(Base):
    __tablename__ = "barbeiros"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, unique=True)
    ativo = Column(Boolean, nullable=False, default=True)

    servicos = relationship(
        "Servico",
        secondary=barbeiros_servicos,
        back_populates="barbeiros",
        lazy="selectin",
    )
