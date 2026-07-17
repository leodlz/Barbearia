import time

from app.database.connection import SessionLocal
from app.services.notificacao_service import processar_pendentes


def executar() -> None:
    while True:
        with SessionLocal() as db:
            processar_pendentes(db)
        time.sleep(30)


if __name__ == "__main__":
    executar()
