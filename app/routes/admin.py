from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
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
from app.schemas.admin import BarbeiroAdminEntrada, ServicoAdminEntrada, StatusEntrada, VincularClienteEntrada
from app.schemas.barbeiro import BarbeiroSaida
from app.schemas.servico import ServicoSaida
from app.services import agendamento_service
from app.services.relogio import hoje_local

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_master)])
STATIC = Path(__file__).parents[1] / "static"


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    hoje = hoje_local()
    return {"agendamentos_hoje": db.query(Agendamento).filter(Agendamento.data == hoje).count(), "proximos": db.query(Agendamento).filter(Agendamento.data >= hoje, Agendamento.status.in_(["agendado", "confirmado"])).count(), "confirmados": db.query(Agendamento).filter(Agendamento.status == "confirmado").count(), "cancelados": db.query(Agendamento).filter(Agendamento.status == "cancelado").count(), "barbeiros_ativos": db.query(Barbeiro).filter(Barbeiro.ativo.is_(True)).count(), "servicos_ativos": db.query(Servico).filter(Servico.ativo.is_(True)).count()}


@router.get("/agendamentos")
def agendamentos(response: Response, data: date | None = None, barbeiro_id: int | None = None, servico_id: int | None = None, status_filtro: str | None = Query(None, alias="status"), busca: str | None = None, pagina: int = Query(1, ge=1), por_pagina: int = Query(20, ge=1, le=100), ordenar: str = Query("data"), direcao: str = Query("asc"), db: Session = Depends(get_db)):
    q = db.query(Agendamento).outerjoin(Cliente)
    if data: q=q.filter(Agendamento.data==data)
    if barbeiro_id: q=q.filter(Agendamento.barbeiro_id==barbeiro_id)
    if servico_id: q=q.filter(Agendamento.servico_id==servico_id)
    if status_filtro: q=q.filter(Agendamento.status==status_filtro)
    if busca: q=q.filter(or_(Agendamento.cliente.ilike(f"%{busca}%"), Cliente.telefone.ilike(f"%{busca}%")))
    colunas = {"data": Agendamento.data, "horario": Agendamento.horario, "status": Agendamento.status, "cliente": Agendamento.cliente}
    if ordenar not in colunas or direcao not in ("asc", "desc"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Ordenação inválida.")
    total = q.count()
    coluna = colunas[ordenar]
    ordem = coluna.desc() if direcao == "desc" else coluna.asc()
    itens = q.order_by(ordem, Agendamento.horario, Agendamento.id).offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(pagina)
    response.headers["X-Page-Size"] = str(por_pagina)
    return [{"id":a.id,"cliente_id":a.cliente_id,"cliente":a.cliente,"telefone":_mascarar_telefone(a.cliente_relacionado.telefone if a.cliente_relacionado else None),"data":a.data,"horario":a.horario,"status":a.status,"barbeiro":a.barbeiro.nome,"servico":a.servico.nome,"preco":str(a.preco_no_agendamento),"duracao_minutos":a.servico.duracao_minutos} for a in itens]


@router.get("/clientes")
def buscar_clientes(busca: str = Query(min_length=2, max_length=100), db: Session = Depends(get_db)):
    termo = f"%{busca.strip()}%"
    clientes = db.query(Cliente).filter(or_(Cliente.nome.ilike(termo), Cliente.telefone.ilike(termo))).order_by(Cliente.nome).limit(20).all()
    return [{"id": cliente.id, "nome": cliente.nome, "telefone": _mascarar_telefone(cliente.telefone)} for cliente in clientes]


@router.put("/agendamentos/{agendamento_id}/cliente")
def vincular_cliente(agendamento_id: int, dados: VincularClienteEntrada, db: Session = Depends(get_db)):
    agendamento = db.get(Agendamento, agendamento_id)
    if not agendamento:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agendamento não encontrado.")
    if agendamento.cliente_id is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este agendamento já está vinculado a um cliente.")
    cliente = db.get(Cliente, dados.cliente_id)
    if not cliente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente não encontrado.")
    agendamento.cliente_id = cliente.id
    agendamento.cliente = cliente.nome
    db.commit()
    return {"id": agendamento.id, "cliente_id": cliente.id, "cliente": cliente.nome, "telefone": _mascarar_telefone(cliente.telefone)}


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
    q=db.query(Agendamento).filter(Agendamento.data>=hoje_local(),Agendamento.status.in_(["agendado","confirmado"]))
    if barbeiro_id:q=q.filter(Agendamento.barbeiro_id==barbeiro_id)
    if servico_id:q=q.filter(Agendamento.servico_id==servico_id)
    return q.count()

def _mascarar_telefone(valor): return f"(**) *****-{valor[-4:]}" if valor else "Não informado"
