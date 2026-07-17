from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_master
from app.models.agendamento import Agendamento
from app.models.barbeiro import Barbeiro
from app.models.cliente import Cliente
from app.models.servico import Servico
from app.models.usuario_master import UsuarioMaster
from app.schemas.admin import BarbeiroAdminEntrada, ServicoAdminEntrada, StatusEntrada
from app.schemas.barbeiro import BarbeiroSaida
from app.schemas.servico import ServicoSaida
from app.services import agendamento_service

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_master)])
STATIC = Path(__file__).parents[1] / "static"


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    hoje = date.today()
    return {"agendamentos_hoje": db.query(Agendamento).filter(Agendamento.data == hoje).count(), "proximos": db.query(Agendamento).filter(Agendamento.data >= hoje, Agendamento.status.in_(["agendado", "confirmado"])).count(), "confirmados": db.query(Agendamento).filter(Agendamento.status == "confirmado").count(), "cancelados": db.query(Agendamento).filter(Agendamento.status == "cancelado").count(), "barbeiros_ativos": db.query(Barbeiro).filter(Barbeiro.ativo.is_(True)).count(), "servicos_ativos": db.query(Servico).filter(Servico.ativo.is_(True)).count()}


@router.get("/agendamentos")
def agendamentos(data: date | None = None, barbeiro_id: int | None = None, servico_id: int | None = None, status_filtro: str | None = Query(None, alias="status"), busca: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Agendamento).outerjoin(Cliente)
    if data: q=q.filter(Agendamento.data==data)
    if barbeiro_id: q=q.filter(Agendamento.barbeiro_id==barbeiro_id)
    if servico_id: q=q.filter(Agendamento.servico_id==servico_id)
    if status_filtro: q=q.filter(Agendamento.status==status_filtro)
    if busca: q=q.filter(or_(Agendamento.cliente.ilike(f"%{busca}%"), Cliente.telefone.ilike(f"%{busca}%")))
    return [{"id":a.id,"cliente":a.cliente,"telefone":_mascarar_telefone(a.cliente_relacionado.telefone if a.cliente_relacionado else None),"data":a.data,"horario":a.horario,"status":a.status,"barbeiro":a.barbeiro.nome,"servico":a.servico.nome,"preco":str(a.preco_no_agendamento),"duracao_minutos":a.servico.duracao_minutos} for a in q.order_by(Agendamento.data,Agendamento.horario).all()]


@router.patch("/agendamentos/{agendamento_id}/status")
def mudar_status(agendamento_id: int, dados: StatusEntrada, db: Session = Depends(get_db)):
    return agendamento_service.alterar_status(db, agendamento_id, dados.status)


@router.get("/servicos", response_model=list[ServicoSaida])
def listar_servicos(db: Session = Depends(get_db)): return db.query(Servico).order_by(Servico.nome).all()

@router.put("/servicos/{servico_id}", response_model=ServicoSaida)
def editar_servico(servico_id: int, dados: ServicoAdminEntrada, db: Session = Depends(get_db)):
    item=db.get(Servico,servico_id)
    if not item: raise HTTPException(404,"Serviço não encontrado.")
    for campo,valor in dados.model_dump().items(): setattr(item,campo,valor)
    db.commit();db.refresh(item);return item

@router.patch("/servicos/{servico_id}/{acao}")
def estado_servico(servico_id: int, acao: str, db: Session = Depends(get_db)):
    item=db.get(Servico,servico_id)
    if not item or acao not in ("ativar","desativar"): raise HTTPException(404,"Serviço ou ação não encontrado.")
    futuros=_futuros(db,servico_id=servico_id);item.ativo=acao=="ativar";db.commit();return {"ativo":item.ativo,"agendamentos_futuros":futuros}

@router.get("/barbeiros", response_model=list[BarbeiroSaida])
def listar_barbeiros(db: Session = Depends(get_db)): return db.query(Barbeiro).order_by(Barbeiro.nome).all()

@router.put("/barbeiros/{barbeiro_id}", response_model=BarbeiroSaida)
def editar_barbeiro(barbeiro_id: int, dados: BarbeiroAdminEntrada, db: Session = Depends(get_db)):
    item=db.get(Barbeiro,barbeiro_id)
    if not item: raise HTTPException(404,"Barbeiro não encontrado.")
    item.nome,item.descricao=dados.nome,dados.descricao
    item.servicos=db.query(Servico).filter(Servico.id.in_(dados.servico_ids)).all() if dados.servico_ids else []
    db.commit();db.refresh(item);return item

@router.patch("/barbeiros/{barbeiro_id}/{acao}")
def estado_barbeiro(barbeiro_id: int, acao: str, db: Session = Depends(get_db)):
    item=db.get(Barbeiro,barbeiro_id)
    if not item or acao not in ("ativar","desativar"): raise HTTPException(404,"Barbeiro ou ação não encontrado.")
    futuros=_futuros(db,barbeiro_id=barbeiro_id);item.ativo=acao=="ativar";db.commit();return {"ativo":item.ativo,"agendamentos_futuros":futuros}

def _futuros(db: Session, barbeiro_id=None, servico_id=None):
    q=db.query(Agendamento).filter(Agendamento.data>=date.today(),Agendamento.status.in_(["agendado","confirmado"]))
    if barbeiro_id:q=q.filter(Agendamento.barbeiro_id==barbeiro_id)
    if servico_id:q=q.filter(Agendamento.servico_id==servico_id)
    return q.count()

def _mascarar_telefone(valor): return f"(**) *****-{valor[-4:]}" if valor else "Não informado"
