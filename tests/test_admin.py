from datetime import date, timedelta

from fastapi.testclient import TestClient

from test_clientes import DADOS


def test_login_master_e_permissoes(client: TestClient) -> None:
    assert client.get('/api/admin/me').status_code == 200
    client.post('/api/admin/logout')
    assert client.get('/api/admin/dashboard').status_code == 401
    assert client.post('/api/admin/login',json={'usuario':'Admin','senha':'errada'}).status_code == 401
    client.post('/api/clientes/registro',json=DADOS)
    assert client.get('/api/admin/dashboard').status_code == 403


def test_master_gerencia_servico_e_barbeiro(client: TestClient) -> None:
    servico=client.post('/servicos',json={'nome':'Corte','preco':'40.00','duracao_minutos':30}).json()
    editado=client.put(f"/api/admin/servicos/{servico['id']}",json={'nome':'Corte premium','descricao':'Completo','preco':'55.00','duracao_minutos':45})
    assert editado.status_code == 200 and editado.json()['preco']=='55.00'
    assert client.patch(f"/api/admin/servicos/{servico['id']}/desativar").json()['ativo'] is False
    assert client.get('/servicos').json() == []
    barbeiro=client.post('/barbeiros',json={'nome':'Carlos'}).json()
    editado=client.put(f"/api/admin/barbeiros/{barbeiro['id']}",json={'nome':'Carlos Silva','descricao':'Especialista','servico_ids':[servico['id']]})
    assert editado.status_code == 200 and len(editado.json()['servicos']) == 1
    assert client.patch(f"/api/admin/barbeiros/{barbeiro['id']}/desativar").json()['ativo'] is False
    assert client.get('/barbeiros').json() == []


def test_cliente_ve_somente_proprios_e_snapshot_de_preco(client: TestClient) -> None:
    servico=client.post('/servicos',json={'nome':'Corte','preco':'40.00','duracao_minutos':30}).json()
    barbeiro=client.post('/barbeiros',json={'nome':'Carlos'}).json();client.post(f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}")
    client.post('/api/admin/logout');client.post('/api/clientes/registro',json=DADOS)
    payload={'barbeiro_id':barbeiro['id'],'servico_id':servico['id'],'data':(date.today()+timedelta(days=2)).isoformat(),'horario':'10:00:00'}
    criado=client.post('/api/clientes/agendamentos',json=payload).json()
    assert criado['preco_no_agendamento']=='40.00'
    meus=client.get('/api/clientes/me/agendamentos').json();assert [a['id'] for a in meus]==[criado['id']]
    cancelado=client.patch(f"/api/clientes/me/agendamentos/{criado['id']}/cancelar").json()
    assert cancelado['status']=='cancelado' and len(client.get('/api/clientes/me/agendamentos').json())==1
    assert client.get('/api/clientes/me/agendamentos/999').status_code==404
