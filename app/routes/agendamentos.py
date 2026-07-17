from fastapi import APIRouter
from app.schemas.agendamento import AgendamentoEntrada
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.agendamento import Agendamento


router = APIRouter()

@router.get("/agendamentos")
def listar_agendamentos(
    db: Session = Depends(get_db),
):
    agendamentos = db.query(Agendamento).all()
    return agendamentos

@router.post("/agendamentos")

def criar_agendamento(
        
    agendamento: AgendamentoEntrada,
    db: Session = Depends(get_db),

):

    novo_agendamento = Agendamento(
    cliente=agendamento.cliente,
    barbeiro=agendamento.barbeiro,
    data=agendamento.data,
    horario=agendamento.horario,
)
    
    db.add(novo_agendamento)

    db.commit()

    db.refresh(novo_agendamento)

    return novo_agendamento