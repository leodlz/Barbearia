import hashlib
import hmac
import os

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.schemas.cliente import ClienteLogin, ClienteRegistro


def registrar_cliente(db: Session, dados: ClienteRegistro) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.cpf == dados.cpf).first()
    if cliente:
        if cliente.senha_hash:
            raise HTTPException(status.HTTP_409_CONFLICT, "CPF já cadastrado. Entre com sua senha.")
        if cliente.telefone != dados.telefone:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Não foi possível validar os dados informados.")
        cliente.nome, cliente.senha_hash = dados.nome, gerar_hash(dados.senha)
    else:
        valores = dados.model_dump(exclude={"senha"})
        cliente = Cliente(**valores, senha_hash=gerar_hash(dados.senha))
        db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def autenticar_cliente(db: Session, dados: ClienteLogin) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.cpf == dados.cpf).first()
    if not cliente or not cliente.senha_hash or not verificar_senha(dados.senha, cliente.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "CPF ou senha inválidos.")
    return cliente


def gerar_hash(senha: str) -> str:
    salt = os.urandom(16)
    derivada = hashlib.scrypt(senha.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${derivada.hex()}"


def verificar_senha(senha: str, armazenada: str) -> bool:
    try:
        _, salt_hex, hash_hex = armazenada.split("$", 2)
        calculada = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(calculada.hex(), hash_hex)
    except (ValueError, TypeError):
        return False
