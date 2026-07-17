from sqlalchemy import Column, ForeignKey, Integer, Table

from app.database.connection import Base


barbeiros_servicos = Table(
    "barbeiros_servicos",
    Base.metadata,
    Column("barbeiro_id", Integer, ForeignKey("barbeiros.id"), primary_key=True),
    Column("servico_id", Integer, ForeignKey("servicos.id"), primary_key=True),
)
