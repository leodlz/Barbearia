from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database.connection import Base


class UsuarioMaster(Base):
    __tablename__ = "usuarios_master"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    usuario = Column(String(50), nullable=False, unique=True)
    senha_hash = Column(String, nullable=False)
    papel = Column(String(20), nullable=False, default="master")
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, nullable=False, default=datetime.now)
