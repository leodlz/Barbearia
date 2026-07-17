from datetime import date, timedelta

from fastapi.testclient import TestClient


def proximo_dia_util() -> date:
    data = date.today() + timedelta(days=1)
    while data.weekday() == 6:
        data += timedelta(days=1)
    return data


def preparar_catalogo(client: TestClient, duracao_minutos: int = 30) -> tuple[int, int]:
    servico = client.post(
        "/servicos",
        json={
            "nome": "Corte",
            "preco": "45.00",
            "duracao_minutos": duracao_minutos,
        },
    ).json()
    barbeiro = client.post("/barbeiros", json={"nome": "Carlos"}).json()
    client.post(f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}")
    return barbeiro["id"], servico["id"]


def test_lista_horarios_dentro_do_expediente(client: TestClient) -> None:
    barbeiro_id, servico_id = preparar_catalogo(client)
    data = proximo_dia_util()

    response = client.get(
        "/disponibilidade",
        params={
            "barbeiro_id": barbeiro_id,
            "servico_id": servico_id,
            "data": data.isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json()["horarios"][0] == "09:00:00"
    assert "12:00:00" not in response.json()["horarios"]
    assert response.json()["horarios"][-1] == "17:30:00"


def test_remove_intervalo_ocupado(client: TestClient) -> None:
    barbeiro_id, servico_id = preparar_catalogo(client)
    data = proximo_dia_util()
    client.post(
        "/agendamentos",
        json={
            "cliente": "Ana",
            "barbeiro_id": barbeiro_id,
            "servico_id": servico_id,
            "data": data.isoformat(),
            "horario": "10:00:00",
        },
    )

    response = client.get(
        "/disponibilidade",
        params={
            "barbeiro_id": barbeiro_id,
            "servico_id": servico_id,
            "data": data.isoformat(),
        },
    )

    assert "10:00:00" not in response.json()["horarios"]
    assert "10:30:00" in response.json()["horarios"]


def test_considera_duracao_e_intervalo(client: TestClient) -> None:
    barbeiro_id, servico_id = preparar_catalogo(client, duracao_minutos=60)
    data = proximo_dia_util()

    response = client.get(
        "/disponibilidade",
        params={
            "barbeiro_id": barbeiro_id,
            "servico_id": servico_id,
            "data": data.isoformat(),
        },
    )

    horarios = response.json()["horarios"]
    assert "11:30:00" not in horarios
    assert "17:30:00" not in horarios
    assert "17:00:00" in horarios


def test_domingo_nao_tem_disponibilidade(client: TestClient) -> None:
    barbeiro_id, servico_id = preparar_catalogo(client)
    domingo = date.today() + timedelta(days=(6 - date.today().weekday()) % 7 or 7)

    response = client.get(
        "/disponibilidade",
        params={
            "barbeiro_id": barbeiro_id,
            "servico_id": servico_id,
            "data": domingo.isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json()["horarios"] == []
