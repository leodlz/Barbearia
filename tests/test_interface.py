from fastapi.testclient import TestClient

from app.main import app


def test_entrega_interface_web_e_arquivos_estaticos() -> None:
    with TestClient(app) as client:
        pagina = client.get("/web")
        estilos = client.get("/static/styles.css")
        script = client.get("/static/app.js")
        interface_script = client.get("/static/ui.js")
        acesso = client.get("/acesso")
        agendar_sem_sessao = client.get("/agendar")

    assert pagina.status_code == 200
    assert "Faça seu agendamento" in pagina.text
    assert estilos.status_code == 200
    assert script.status_code == 200
    assert interface_script.status_code == 200
    assert "Abrir menu" in interface_script.text
    assert acesso.status_code == 200
    assert "Nome completo" in acesso.text
    assert agendar_sem_sessao.status_code == 401
