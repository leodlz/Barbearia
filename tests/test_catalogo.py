from fastapi.testclient import TestClient


def criar_servico(client: TestClient) -> dict:
    response = client.post(
        "/servicos",
        json={
            "nome": "Corte",
            "descricao": "Corte tradicional",
            "preco": "45.90",
            "duracao_minutos": 30,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def criar_barbeiro(client: TestClient) -> dict:
    response = client.post("/barbeiros", json={"nome": "Carlos"})
    assert response.status_code == 201, response.text
    return response.json()


def test_cria_lista_e_busca_servico(client: TestClient) -> None:
    servico = criar_servico(client)

    assert client.get(f"/servicos/{servico['id']}").json() == servico
    assert client.get("/servicos").json() == [servico]


def test_impede_servico_com_nome_duplicado(client: TestClient) -> None:
    criar_servico(client)

    response = client.post(
        "/servicos",
        json={
            "nome": "Corte",
            "preco": "50.00",
            "duracao_minutos": 45,
        },
    )

    assert response.status_code == 409


def test_cria_lista_e_busca_barbeiro(client: TestClient) -> None:
    barbeiro = criar_barbeiro(client)

    assert client.get(f"/barbeiros/{barbeiro['id']}").json() == barbeiro
    assert client.get("/barbeiros").json() == [barbeiro]


def test_associa_e_remove_servico_do_barbeiro(client: TestClient) -> None:
    barbeiro = criar_barbeiro(client)
    servico = criar_servico(client)

    associado = client.post(
        f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}"
    )
    assert associado.status_code == 200
    assert associado.json()["servicos"] == [servico]

    repetido = client.post(
        f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}"
    )
    assert repetido.status_code == 409

    removido = client.delete(
        f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}"
    )
    assert removido.status_code == 204
    assert client.get(f"/barbeiros/{barbeiro['id']}").json()["servicos"] == []
