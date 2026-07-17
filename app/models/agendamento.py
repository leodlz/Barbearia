from datetime import datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Time
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

    preco_no_agendamento = Column(Numeric(10, 2), nullable=False)

    criado_em = Column(DateTime, nullable=False, default=datetime.now)

    barbeiro = relationship("Barbeiro", lazy="joined")

    servico = relationship("Servico", lazy="joined")

    cliente_relacionado = relationship("Cliente", back_populates="agendamentos")

    notificacao = relationship("Notificacao", back_populates="agendamento", uselist=False)
