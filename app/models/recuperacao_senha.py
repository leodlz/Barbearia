from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.database.connection import Base


class RecuperacaoSenha(Base):
    __tablename__ = "recuperacoes_senha"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    codigo_hash = Column(String, nullable=False)
    expira_em = Column(DateTime, nullable=False)
    tentativas = Column(Integer, nullable=False, default=0)
    usado_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, nullable=False)
