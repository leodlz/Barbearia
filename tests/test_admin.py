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


def test_master_troca_senha_com_validacoes(client: TestClient) -> None:
    endpoint = '/api/admin/senha'
    assert client.put(endpoint, json={
        'senha_atual': 'incorreta',
        'nova_senha': 'nova-senha-segura',
        'confirmar_nova_senha': 'nova-senha-segura',
    }).status_code == 400
    assert client.put(endpoint, json={
        'senha_atual': 'senha-admin',
        'nova_senha': 'nova-senha-segura',
        'confirmar_nova_senha': 'outra-senha-segura',
    }).status_code == 422
    assert client.put(endpoint, json={
        'senha_atual': 'senha-admin',
        'nova_senha': 'nova-senha-segura',
        'confirmar_nova_senha': 'nova-senha-segura',
    }).status_code == 204
    assert client.get('/api/admin/me').status_code == 200
    client.post('/api/admin/logout')
    assert client.post('/api/admin/login', json={'usuario': 'Admin', 'senha': 'senha-admin'}).status_code == 401
    assert client.post('/api/admin/login', json={'usuario': 'Admin', 'senha': 'nova-senha-segura'}).status_code == 200


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


def test_master_busca_cliente_e_vincula_agendamento_legado(client: TestClient) -> None:
    servico = client.post('/servicos', json={'nome': 'Corte', 'preco': '40.00', 'duracao_minutos': 30}).json()
    barbeiro = client.post('/barbeiros', json={'nome': 'Carlos'}).json()
    client.post(f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}")
    legado = client.post('/agendamentos', json={
        'cliente': 'Cadastro antigo',
        'barbeiro_id': barbeiro['id'],
        'servico_id': servico['id'],
        'data': (date.today() + timedelta(days=2)).isoformat(),
        'horario': '11:00:00',
    }).json()
    client.post('/api/admin/logout')
    cliente = client.post('/api/clientes/registro', json=DADOS).json()
    client.post('/api/clientes/logout')
    client.post('/api/admin/login', json={'usuario': 'Admin', 'senha': 'senha-admin'})

    encontrados = client.get('/api/admin/clientes', params={'busca': DADOS['nome'][:4]}).json()
    assert encontrados == [{'id': cliente['id'], 'nome': DADOS['nome'], 'telefone': f"(**) *****-{DADOS['telefone'][-4:]}"}]
    assert 'cpf' not in encontrados[0]
    vinculado = client.put(f"/api/admin/agendamentos/{legado['id']}/cliente", json={'cliente_id': cliente['id']})
    assert vinculado.status_code == 200
    assert vinculado.json()['cliente'] == DADOS['nome']
    assert client.put(f"/api/admin/agendamentos/{legado['id']}/cliente", json={'cliente_id': cliente['id']}).status_code == 409

    client.post('/api/admin/logout')
    client.post('/api/clientes/login', json={'cpf': DADOS['cpf'], 'senha': DADOS['senha']})
    assert [item['id'] for item in client.get('/api/clientes/me/agendamentos').json()] == [legado['id']]


def test_master_pagina_e_ordena_agendamentos(client: TestClient) -> None:
    servico = client.post('/servicos', json={'nome': 'Corte', 'preco': '40.00', 'duracao_minutos': 30}).json()
    barbeiro = client.post('/barbeiros', json={'nome': 'Carlos'}).json()
    client.post(f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}")
    for indice, nome in enumerate(('Ana', 'Bia', 'Caio')):
        criado = client.post('/agendamentos', json={'cliente': nome, 'barbeiro_id': barbeiro['id'], 'servico_id': servico['id'], 'data': (date.today() + timedelta(days=2)).isoformat(), 'horario': f'{9 + indice:02d}:00:00'})
        assert criado.status_code == 201, criado.text

    primeira = client.get('/api/admin/agendamentos', params={'por_pagina': 2, 'ordenar': 'cliente', 'direcao': 'desc'})
    assert primeira.status_code == 200
    assert primeira.headers['X-Total-Count'] == '3'
    assert [item['cliente'] for item in primeira.json()] == ['Caio', 'Bia']
    segunda = client.get('/api/admin/agendamentos', params={'por_pagina': 2, 'pagina': 2, 'ordenar': 'cliente', 'direcao': 'desc'})
    assert [item['cliente'] for item in segunda.json()] == ['Ana']
    assert client.get('/api/admin/agendamentos', params={'ordenar': 'campo-inexistente'}).status_code == 422
