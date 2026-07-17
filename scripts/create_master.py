import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func

from app.database.connection import SessionLocal
from app.models.usuario_master import UsuarioMaster
from app.services.cliente_service import gerar_hash


def main() -> None:
    nome = os.environ.get("MASTER_NAME")
    usuario = os.environ.get("MASTER_USER")
    senha = os.environ.get("MASTER_PASSWORD")
    if not all((nome, usuario, senha)):
        raise SystemExit("Defina MASTER_NAME, MASTER_USER e MASTER_PASSWORD.")
    with SessionLocal() as db:
        existente = db.query(UsuarioMaster).filter(func.lower(UsuarioMaster.usuario) == usuario.lower()).first()
        if existente:
            print("Usuário master já existe; nenhuma alteração foi feita.")
            return
        db.add(UsuarioMaster(nome=nome, usuario=usuario, senha_hash=gerar_hash(senha), papel="master", ativo=True))
        db.commit()
    print("Usuário master criado com sucesso.")


if __name__ == "__main__": main()
