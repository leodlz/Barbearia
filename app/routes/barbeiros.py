from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.barbeiro import BarbeiroEntrada, BarbeiroSaida
from app.services import barbeiro_service


router = APIRouter(prefix="/barbeiros", tags=["Barbeiros"])


@router.get("", response_model=list[BarbeiroSaida])
def listar_barbeiros(
    somente_ativos: bool = False,
    db: Session = Depends(get_db),
):
    return barbeiro_service.listar_barbeiros(db, somente_ativos)


@router.get("/{barbeiro_id}", response_model=BarbeiroSaida)
def buscar_barbeiro(barbeiro_id: int, db: Session = Depends(get_db)):
    return barbeiro_service.obter_barbeiro(db, barbeiro_id)


@router.post(
    "",
    response_model=BarbeiroSaida,
    status_code=status.HTTP_201_CREATED,
)
def criar_barbeiro(
    barbeiro: BarbeiroEntrada,
    db: Session = Depends(get_db),
):
    return barbeiro_service.criar_barbeiro(db, barbeiro)


@router.post(
    "/{barbeiro_id}/servicos/{servico_id}",
    response_model=BarbeiroSaida,
)
def associar_servico(
    barbeiro_id: int,
    servico_id: int,
    db: Session = Depends(get_db),
):
    return barbeiro_service.associar_servico(db, barbeiro_id, servico_id)


@router.delete(
    "/{barbeiro_id}/servicos/{servico_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remover_servico(
    barbeiro_id: int,
    servico_id: int,
    db: Session = Depends(get_db),
) -> Response:
    barbeiro_service.remover_servico(db, barbeiro_id, servico_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
