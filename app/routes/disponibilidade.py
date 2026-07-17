from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.disponibilidade import DisponibilidadeSaida
from app.services import disponibilidade_service


router = APIRouter(prefix="/disponibilidade", tags=["Disponibilidade"])


@router.get("", response_model=DisponibilidadeSaida)
def consultar_disponibilidade(
    barbeiro_id: int,
    servico_id: int,
    data: date,
    db: Session = Depends(get_db),
):
    return disponibilidade_service.listar_horarios(
        db,
        barbeiro_id,
        servico_id,
        data,
    )
