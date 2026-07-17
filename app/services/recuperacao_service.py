import os
import secrets
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from twilio.rest import Client

from app.models.cliente import Cliente
from app.models.recuperacao_senha import RecuperacaoSenha
from app.schemas.cliente import RecuperacaoConfirmacao
from app.services.cliente_service import gerar_hash, verificar_senha
from app.services.relogio import agora_local


def solicitar(db: Session, cpf: str) -> str | None:
    cliente = db.query(Cliente).filter(Cliente.cpf == cpf).first()
    if not cliente:
        return None
    agora = agora_local()
    recente = db.query(RecuperacaoSenha).filter(RecuperacaoSenha.cliente_id == cliente.id).order_by(RecuperacaoSenha.criado_em.desc()).first()
    if recente and recente.criado_em > agora - timedelta(seconds=60):
        return None
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    db.add(RecuperacaoSenha(cliente_id=cliente.id, codigo_hash=gerar_hash(codigo), expira_em=agora + timedelta(minutes=10), tentativas=0, criado_em=agora))
    db.commit()
    if os.getenv("NOTIFICACAO_PROVEDOR", "simulado") == "simulado":
        return codigo
    destino = f"+55{cliente.telefone}"
    origem = os.environ["TWILIO_FROM_NUMBER"]
    if os.getenv("NOTIFICACAO_CANAL", "sms") == "whatsapp":
        destino, origem = f"whatsapp:{destino}", f"whatsapp:{origem}"
    Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]).messages.create(body=f"Seu código de recuperação é {codigo}. Ele expira em 10 minutos.", from_=origem, to=destino)
    return None


def confirmar(db: Session, dados: RecuperacaoConfirmacao) -> None:
    cliente = db.query(Cliente).filter(Cliente.cpf == dados.cpf).first()
    if not cliente or dados.nova_senha != dados.confirmar_nova_senha:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Código ou dados inválidos.")
    token = db.query(RecuperacaoSenha).filter(RecuperacaoSenha.cliente_id == cliente.id, RecuperacaoSenha.usado_em.is_(None)).order_by(RecuperacaoSenha.criado_em.desc()).first()
    agora = agora_local()
    if not token or token.expira_em < agora or token.tentativas >= 5:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Código inválido ou expirado.")
    if not verificar_senha(dados.codigo, token.codigo_hash):
        token.tentativas += 1
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Código inválido ou expirado.")
    cliente.senha_hash = gerar_hash(dados.nova_senha)
    token.usado_em = agora
    db.commit()
