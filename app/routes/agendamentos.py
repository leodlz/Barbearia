from fastapi import APIRouter

router = APIRouter()

@router.get("/agendamentos")

def listar_agendamentos():

        return {'mensagem': 'Lista de Agendamentos'}