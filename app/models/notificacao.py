from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(Integer, primary_key=True, index=True)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=False, unique=True)
    canal = Column(String(20), nullable=False)
    enviar_em = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pendente")
    tentativas = Column(Integer, nullable=False, default=0)
    enviado_em = Column(DateTime, nullable=True)
    provedor_id = Column(String, nullable=True)
    ultimo_erro = Column(String, nullable=True)

    agendamento = relationship("Agendamento", back_populates="notificacao")
