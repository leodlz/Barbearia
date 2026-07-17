from fastapi.testclient import TestClient
from datetime import date, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker
from app.models.notificacao import Notificacao


def cpf_teste() -> str:
    cpf = [int(digito) for digito in "529982247"]
    for tamanho in (9, 10):
        soma = sum(cpf[i] * (tamanho + 1 - i) for i in range(tamanho))
        cpf.append((soma * 10 % 11) % 10)
    return "".join(map(str, cpf))


DADOS = {"nome": "Leonardo Luz", "telefone": "48" + "9" * 9, "cpf": cpf_teste(), "senha": "senha-segura"}


def test_normaliza_cliente_e_cria_sessao(client: TestClient) -> None:
    response = client.post("/api/clientes/registro", json=DADOS)
    assert response.status_code == 201
    assert response.json()["telefone"] == "48" + "9" * 9
    assert "cpf" not in response.json()
    assert client.get("/api/clientes/me").json()["nome"] == "Leonardo Luz"


def test_rejeita_cpf_invalido_e_repetido(client: TestClient) -> None:
    assert client.post("/api/clientes/registro", json={**DADOS, "cpf": "123"}).status_code == 422
    assert client.post("/api/clientes/registro", json={**DADOS, "cpf": "1" * 11}).status_code == 422


def test_impede_cpf_duplicado_e_permite_login(client: TestClient) -> None:
    client.post("/api/clientes/registro", json=DADOS)
    assert client.post("/api/clientes/registro", json=DADOS).status_code == 409
    client.post("/api/clientes/logout")
    login = client.post("/api/clientes/login", json={"cpf": DADOS["cpf"], "senha": DADOS["senha"]})
    assert login.status_code == 200
    assert "senha" not in login.json() and "cpf" not in login.json()
    assert client.post("/api/clientes/login", json={"cpf": DADOS["cpf"], "senha": "errada"}).status_code == 401


def test_logout_remove_sessao(client: TestClient) -> None:
    client.post("/api/clientes/registro", json=DADOS)
    assert client.post("/api/clientes/logout").status_code == 204
    assert client.get("/api/clientes/me").status_code == 401


def test_agendamento_exige_sessao_e_cria_lembrete(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    servico=client.post('/servicos',json={'nome':'Corte','preco':'40.00','duracao_minutos':30}).json()
    barbeiro=client.post('/barbeiros',json={'nome':'Carlos'}).json()
    client.post(f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}")
    client.post('/api/admin/logout')
    payload={'barbeiro_id':barbeiro['id'],'servico_id':servico['id'],'data':(date.today()+timedelta(days=2)).isoformat(),'horario':'10:00:00'}
    assert client.post('/api/clientes/agendamentos',json=payload).status_code == 401
    client.post('/api/clientes/registro',json=DADOS)
    assert client.post('/api/clientes/agendamentos',json=payload).status_code == 201
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Notificacao)) == 1


def test_recupera_senha_com_codigo_temporario(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv('NOTIFICACAO_PROVEDOR', 'simulado')
    client.post('/api/clientes/registro', json=DADOS)
    client.post('/api/clientes/logout')
    resposta = client.post('/api/clientes/recuperacao/solicitar', json={'cpf': DADOS['cpf']})
    codigo = resposta.json()['codigo_teste']
    assert client.post('/api/clientes/recuperacao/confirmar', json={'cpf': DADOS['cpf'], 'codigo': '000000', 'nova_senha': 'senha-nova-segura', 'confirmar_nova_senha': 'senha-nova-segura'}).status_code == 400
    assert client.post('/api/clientes/recuperacao/confirmar', json={'cpf': DADOS['cpf'], 'codigo': codigo, 'nova_senha': 'senha-nova-segura', 'confirmar_nova_senha': 'senha-nova-segura'}).status_code == 204
    assert client.post('/api/clientes/login', json={'cpf': DADOS['cpf'], 'senha': DADOS['senha']}).status_code == 401
    assert client.post('/api/clientes/login', json={'cpf': DADOS['cpf'], 'senha': 'senha-nova-segura'}).status_code == 200


def test_recuperacao_nao_revela_cpf_inexistente(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv('NOTIFICACAO_PROVEDOR', 'simulado')
    resposta = client.post('/api/clientes/recuperacao/solicitar', json={'cpf': cpf_teste()})
    assert resposta.status_code == 200
    assert 'codigo_teste' not in resposta.json()
