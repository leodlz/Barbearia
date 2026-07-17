from datetime import datetime, timezone

from app.services.relogio import agora_local


def test_relogio_respeita_timezone_configurado(monkeypatch) -> None:
    monkeypatch.setenv("BARBEARIA_TIMEZONE", "UTC")
    diferenca = abs((agora_local() - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())
    assert diferenca < 2
