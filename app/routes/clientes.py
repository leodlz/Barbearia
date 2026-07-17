from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.cliente import Cliente
from app.schemas.agendamento import AgendamentoClienteEntrada, AgendamentoEntrada, AgendamentoSaida
from app.schemas.cliente import ClienteLogin, ClienteRegistro, ClienteSaida
from app.services import agendamento_service, cliente_service, notificacao_service

router = APIRouter(tags=["Clientes"])
STATIC = Path(__file__).parents[1] / "static"

def cliente_da_sessao(request: Request, db: Session) -> Cliente:
    cliente_id = request.session.get("cliente_id")
    cliente = db.get(Cliente, cliente_id) if cliente_id else None
    if not cliente:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada. Entre novamente.")
    return cliente

@router.get("/acesso", include_in_schema=False)
def acesso(): return FileResponse(STATIC / "acesso.html")

@router.get("/agendar", include_in_schema=False)
def agendar(request: Request):
    if not request.session.get("cliente_id"):
        return FileResponse(STATIC / "acesso.html", status_code=401)
    return FileResponse(STATIC / "index.html")

@router.post("/api/clientes/registro", response_model=ClienteSaida, status_code=201)
def registrar(dados: ClienteRegistro, request: Request, db: Session = Depends(get_db)):
    cliente = cliente_service.registrar_cliente(db, dados)
    request.session.clear(); request.session["cliente_id"] = cliente.id
    return cliente

@router.post("/api/clientes/login", response_model=ClienteSaida)
def entrar(dados: ClienteLogin, request: Request, db: Session = Depends(get_db)):
    cliente = cliente_service.autenticar_cliente(db, dados)
    request.session.clear(); request.session["cliente_id"] = cliente.id
    return cliente

@router.get("/api/clientes/me", response_model=ClienteSaida)
def me(request: Request, db: Session = Depends(get_db)):
    return cliente_da_sessao(request, db)

@router.post("/api/clientes/logout", status_code=204)
def sair(request: Request): request.session.clear()

@router.post("/api/clientes/agendamentos", response_model=AgendamentoSaida, status_code=201)
def criar(dados: AgendamentoClienteEntrada, request: Request, db: Session = Depends(get_db)):
    cliente = cliente_da_sessao(request, db)
    entrada = AgendamentoEntrada(cliente=cliente.nome, **dados.model_dump())
    agendamento = agendamento_service.criar_agendamento(db, entrada, cliente.id)
    notificacao_service.agendar_lembrete(db, agendamento)
    return agendamento
