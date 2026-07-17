from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.servico import ServicoEntrada, ServicoSaida
from app.services import servico_service


router = APIRouter(prefix="/servicos", tags=["Serviços"])


@router.get("", response_model=list[ServicoSaida])
def listar_servicos(
    somente_ativos: bool = False,
    db: Session = Depends(get_db),
):
    return servico_service.listar_servicos(db, somente_ativos)


@router.get("/{servico_id}", response_model=ServicoSaida)
def buscar_servico(servico_id: int, db: Session = Depends(get_db)):
    return servico_service.obter_servico(db, servico_id)


@router.post(
    "",
    response_model=ServicoSaida,
    status_code=status.HTTP_201_CREATED,
)
def criar_servico(
    servico: ServicoEntrada,
    db: Session = Depends(get_db),
):
    return servico_service.criar_servico(db, servico)
