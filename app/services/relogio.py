import os
from datetime import datetime
from zoneinfo import ZoneInfo


def agora_local() -> datetime:
    """Retorna o horário civil da barbearia, sem tzinfo para o schema legado."""
    fuso = ZoneInfo(os.getenv("BARBEARIA_TIMEZONE", "America/Sao_Paulo"))
    return datetime.now(fuso).replace(tzinfo=None)


def hoje_local():
    return agora_local().date()
