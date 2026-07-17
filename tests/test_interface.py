from fastapi.testclient import TestClient

from app.main import app


def test_entrega_interface_web_e_arquivos_estaticos() -> None:
    with TestClient(app) as client:
        pagina = client.get("/web")
        estilos = client.get("/static/styles.css")
        script = client.get("/static/app.js")

    assert pagina.status_code == 200
    assert "Faça seu agendamento" in pagina.text
    assert estilos.status_code == 200
    assert script.status_code == 200
