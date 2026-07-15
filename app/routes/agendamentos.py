from fastapi import APIRouter
from app.schemas.agendamento import AgendamentoEntrada


router = APIRouter()

@router.get("/agendamentos")

def listar_agendamentos():

        return {'mensagem': 'Lista de Agendamentos'}

@router.post("/agendamentos")

def criar_agendamento(agendamento: AgendamentoEntrada):
        
        return agendamento