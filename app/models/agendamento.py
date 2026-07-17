from app.database.connection import Base
from sqlalchemy import Column, Integer, String, Time, Date


class Agendamento(Base):

    __tablename__ = 'agendamentos'

    id = Column(Integer, primary_key=True, index=True)

    cliente = Column(String, nullable=False)

    barbeiro = Column(String, nullable=False)

    data = Column(Date, nullable=False)

    horario = Column(Time, nullable=False)

    status = Column(String, nullable=False, default="agendado")