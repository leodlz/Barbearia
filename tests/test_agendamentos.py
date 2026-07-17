from datetime import date, timedelta, time

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models.agendamento import Agendamento


def dados_agendamento(**alteracoes) -> dict:
    dados = {
        "cliente": "Ana",
        "barbeiro": "Carlos",
        "data": (date.today() + timedelta(days=2)).isoformat(),
        "horario": "09:00:00",
    }
    dados.update(alteracoes)
    return dados


def test_cria_agendamento(client: TestClient) -> None:
    response = client.post("/agendamentos", json=dados_agendamento())

    assert response.status_code == 201
    assert response.json()["status"] == "agendado"
    assert response.json()["cliente"] == "Ana"


def test_impede_conflito_para_o_mesmo_barbeiro(client: TestClient) -> None:
    client.post("/agendamentos", json=dados_agendamento())

    response = client.post(
        "/agendamentos",
        json=dados_agendamento(cliente="Bia"),
    )

    assert response.status_code == 409


def test_permite_mesmo_horario_para_barbeiros_diferentes(
    client: TestClient,
) -> None:
    client.post("/agendamentos", json=dados_agendamento())

    response = client.post(
        "/agendamentos",
        json=dados_agendamento(barbeiro="João"),
    )

    assert response.status_code == 201


def test_lista_agendamentos(client: TestClient) -> None:
    client.post("/agendamentos", json=dados_agendamento())
    client.post(
        "/agendamentos",
        json=dados_agendamento(barbeiro="João"),
    )

    response = client.get("/agendamentos")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_busca_agendamento_por_id(client: TestClient) -> None:
    criado = client.post("/agendamentos", json=dados_agendamento()).json()

    response = client.get(f"/agendamentos/{criado['id']}")

    assert response.status_code == 200
    assert response.json() == criado


def test_retorna_404_para_agendamento_inexistente(client: TestClient) -> None:
    response = client.get("/agendamentos/999")

    assert response.status_code == 404


def test_cancela_agendamento(client: TestClient) -> None:
    criado = client.post("/agendamentos", json=dados_agendamento()).json()

    response = client.patch(f"/agendamentos/{criado['id']}/cancelar")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelado"


def test_impede_cancelamento_duplicado(client: TestClient) -> None:
    criado = client.post("/agendamentos", json=dados_agendamento()).json()
    client.patch(f"/agendamentos/{criado['id']}/cancelar")

    response = client.patch(f"/agendamentos/{criado['id']}/cancelar")

    assert response.status_code == 409


def test_libera_horario_apos_cancelamento(client: TestClient) -> None:
    criado = client.post("/agendamentos", json=dados_agendamento()).json()
    client.patch(f"/agendamentos/{criado['id']}/cancelar")

    response = client.post(
        "/agendamentos",
        json=dados_agendamento(cliente="Bia"),
    )

    assert response.status_code == 201


def test_rejeita_agendamento_no_passado(client: TestClient) -> None:
    response = client.post(
        "/agendamentos",
        json=dados_agendamento(data=(date.today() - timedelta(days=1)).isoformat()),
    )

    assert response.status_code == 422


def test_conclui_agendamento_decorrido(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        agendamento = Agendamento(
            cliente="Ana",
            barbeiro="Carlos",
            data=date.today() - timedelta(days=1),
            horario=time(9),
        )
        db.add(agendamento)
        db.commit()
        agendamento_id = agendamento.id

    response = client.patch(f"/agendamentos/{agendamento_id}/concluir")

    assert response.status_code == 200
    assert response.json()["status"] == "concluido"


def test_registra_falta_em_agendamento_decorrido(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        agendamento = Agendamento(
            cliente="Ana",
            barbeiro="Carlos",
            data=date.today() - timedelta(days=1),
            horario=time(9),
        )
        db.add(agendamento)
        db.commit()
        agendamento_id = agendamento.id

    response = client.patch(f"/agendamentos/{agendamento_id}/falta")

    assert response.status_code == 200
    assert response.json()["status"] == "faltou"
