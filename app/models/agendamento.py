from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Agendamento(Base):

    __tablename__ = 'agendamentos'

    id = Column(Integer, primary_key=True, index=True)

    cliente = Column(String, nullable=False)

    barbeiro_id = Column(Integer, ForeignKey("barbeiros.id"), nullable=False)

    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=False)

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)

    data = Column(Date, nullable=False)

    horario = Column(Time, nullable=False)

    status = Column(String, nullable=False, default="agendado")

    barbeiro = relationship("Barbeiro", lazy="joined")

    servico = relationship("Servico", lazy="joined")

    cliente_relacionado = relationship("Cliente", back_populates="agendamentos")

    notificacao = relationship("Notificacao", back_populates="agendamento", uselist=False)
