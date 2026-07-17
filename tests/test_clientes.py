from fastapi.testclient import TestClient
from datetime import date, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker
from app.models.notificacao import Notificacao


DADOS = {"nome": "Leonardo Luz", "telefone": "(48) 99999-9999", "cpf": "529.982.247-25"}


def test_normaliza_cliente_e_cria_sessao(client: TestClient) -> None:
    response = client.post("/api/clientes/acesso", json=DADOS)
    assert response.status_code == 200
    assert response.json()["telefone"] == "48999999999"
    assert "cpf" not in response.json()
    assert client.get("/api/clientes/me").json()["nome"] == "Leonardo Luz"


def test_rejeita_cpf_invalido_e_repetido(client: TestClient) -> None:
    assert client.post("/api/clientes/acesso", json={**DADOS, "cpf": "123"}).status_code == 422
    assert client.post("/api/clientes/acesso", json={**DADOS, "cpf": "11111111111"}).status_code == 422


def test_reutiliza_cliente_sem_duplicar(client: TestClient) -> None:
    primeiro = client.post("/api/clientes/acesso", json=DADOS).json()
    segundo = client.post("/api/clientes/acesso", json={**DADOS, "nome": "Leonardo da Luz"}).json()
    assert primeiro["id"] == segundo["id"]
    assert segundo["nome"] == "Leonardo da Luz"


def test_logout_remove_sessao(client: TestClient) -> None:
    client.post("/api/clientes/acesso", json=DADOS)
    assert client.post("/api/clientes/logout").status_code == 204
    assert client.get("/api/clientes/me").status_code == 401


def test_agendamento_exige_sessao_e_cria_lembrete(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    servico=client.post('/servicos',json={'nome':'Corte','preco':'40.00','duracao_minutos':30}).json()
    barbeiro=client.post('/barbeiros',json={'nome':'Carlos'}).json()
    client.post(f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}")
    payload={'barbeiro_id':barbeiro['id'],'servico_id':servico['id'],'data':(date.today()+timedelta(days=2)).isoformat(),'horario':'10:00:00'}
    assert client.post('/api/clientes/agendamentos',json=payload).status_code == 401
    client.post('/api/clientes/acesso',json=DADOS)
    assert client.post('/api/clientes/agendamentos',json=payload).status_code == 201
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Notificacao)) == 1
