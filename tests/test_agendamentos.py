from datetime import date, timedelta, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models.agendamento import Agendamento


@pytest.fixture
def catalogo(client: TestClient) -> dict[str, int]:
    servico = client.post(
        "/servicos",
        json={"nome": "Corte", "preco": "45.00", "duracao_minutos": 30},
    ).json()
    barbeiro = client.post("/barbeiros", json={"nome": "Carlos"}).json()
    client.post(f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}")
    return {"barbeiro_id": barbeiro["id"], "servico_id": servico["id"]}


def dados_agendamento(catalogo: dict[str, int], **alteracoes) -> dict:
    dados = {
        "cliente": "Ana",
        **catalogo,
        "data": (date.today() + timedelta(days=2)).isoformat(),
        "horario": "09:00:00",
    }
    dados.update(alteracoes)
    return dados


def test_cria_agendamento(client: TestClient, catalogo: dict[str, int]) -> None:
    response = client.post("/agendamentos", json=dados_agendamento(catalogo))

    assert response.status_code == 201
    assert response.json()["status"] == "agendado"
    assert response.json()["barbeiro"]["nome"] == "Carlos"
    assert response.json()["servico"]["duracao_minutos"] == 30


def test_impede_sobreposicao_para_o_mesmo_barbeiro(
    client: TestClient,
    catalogo: dict[str, int],
) -> None:
    client.post("/agendamentos", json=dados_agendamento(catalogo))

    response = client.post(
        "/agendamentos",
        json=dados_agendamento(catalogo, cliente="Bia", horario="09:15:00"),
    )

    assert response.status_code == 409


def test_permite_agendamento_no_final_do_intervalo(
    client: TestClient,
    catalogo: dict[str, int],
) -> None:
    client.post("/agendamentos", json=dados_agendamento(catalogo))

    response = client.post(
        "/agendamentos",
        json=dados_agendamento(catalogo, cliente="Bia", horario="09:30:00"),
    )

    assert response.status_code == 201


def test_permite_mesmo_horario_para_barbeiros_diferentes(
    client: TestClient,
    catalogo: dict[str, int],
) -> None:
    client.post("/agendamentos", json=dados_agendamento(catalogo))
    outro = client.post("/barbeiros", json={"nome": "João"}).json()
    client.post(
        f"/barbeiros/{outro['id']}/servicos/{catalogo['servico_id']}"
    )

    response = client.post(
        "/agendamentos",
        json=dados_agendamento(catalogo, barbeiro_id=outro["id"]),
    )

    assert response.status_code == 201


def test_lista_agendamentos(client: TestClient, catalogo: dict[str, int]) -> None:
    client.post("/agendamentos", json=dados_agendamento(catalogo))
    client.post(
        "/agendamentos",
        json=dados_agendamento(catalogo, horario="10:00:00"),
    )

    response = client.get("/agendamentos")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_busca_agendamento_por_id(
    client: TestClient,
    catalogo: dict[str, int],
) -> None:
    criado = client.post("/agendamentos", json=dados_agendamento(catalogo)).json()

    response = client.get(f"/agendamentos/{criado['id']}")

    assert response.status_code == 200
    assert response.json() == criado


def test_retorna_404_para_agendamento_inexistente(client: TestClient) -> None:
    response = client.get("/agendamentos/999")

    assert response.status_code == 404


def test_cancela_agendamento(client: TestClient, catalogo: dict[str, int]) -> None:
    criado = client.post("/agendamentos", json=dados_agendamento(catalogo)).json()

    response = client.patch(f"/agendamentos/{criado['id']}/cancelar")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelado"


def test_impede_cancelamento_duplicado(
    client: TestClient,
    catalogo: dict[str, int],
) -> None:
    criado = client.post("/agendamentos", json=dados_agendamento(catalogo)).json()
    client.patch(f"/agendamentos/{criado['id']}/cancelar")

    response = client.patch(f"/agendamentos/{criado['id']}/cancelar")

    assert response.status_code == 409


def test_libera_horario_apos_cancelamento(
    client: TestClient,
    catalogo: dict[str, int],
) -> None:
    criado = client.post("/agendamentos", json=dados_agendamento(catalogo)).json()
    client.patch(f"/agendamentos/{criado['id']}/cancelar")

    response = client.post(
        "/agendamentos",
        json=dados_agendamento(catalogo, cliente="Bia"),
    )

    assert response.status_code == 201


def test_rejeita_agendamento_no_passado(
    client: TestClient,
    catalogo: dict[str, int],
) -> None:
    response = client.post(
        "/agendamentos",
        json=dados_agendamento(
            catalogo,
            data=(date.today() - timedelta(days=1)).isoformat(),
        ),
    )

    assert response.status_code == 422


def test_rejeita_servico_nao_realizado_pelo_barbeiro(
    client: TestClient,
    catalogo: dict[str, int],
) -> None:
    outro_servico = client.post(
        "/servicos",
        json={"nome": "Barba", "preco": "30.00", "duracao_minutos": 20},
    ).json()

    response = client.post(
        "/agendamentos",
        json=dados_agendamento(catalogo, servico_id=outro_servico["id"]),
    )

    assert response.status_code == 409


def test_conclui_agendamento_decorrido(
    client: TestClient,
    session_factory: sessionmaker[Session],
    catalogo: dict[str, int],
) -> None:
    with session_factory() as db:
        agendamento = Agendamento(
            cliente="Ana",
            **catalogo,
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
    catalogo: dict[str, int],
) -> None:
    with session_factory() as db:
        agendamento = Agendamento(
            cliente="Ana",
            **catalogo,
            data=date.today() - timedelta(days=1),
            horario=time(9),
        )
        db.add(agendamento)
        db.commit()
        agendamento_id = agendamento.id

    response = client.patch(f"/agendamentos/{agendamento_id}/falta")

    assert response.status_code == 200
    assert response.json()["status"] == "faltou"
