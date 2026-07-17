import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from twilio.rest import Client

from app.models.notificacao import Notificacao
from app.services.relogio import agora_local


def agendar_lembrete(db: Session, agendamento) -> None:
    enviar_em = datetime.combine(agendamento.data, agendamento.horario) - timedelta(hours=24)
    db.add(Notificacao(agendamento_id=agendamento.id, canal=os.getenv("NOTIFICACAO_CANAL", "sms"), enviar_em=max(enviar_em, agora_local()), status="pendente", tentativas=0))
    db.commit()


def processar_pendentes(db: Session) -> int:
    pendentes = db.query(Notificacao).filter(Notificacao.status == "pendente", Notificacao.enviar_em <= agora_local()).all()
    enviados = 0
    for item in pendentes:
        if item.agendamento.status != "agendado":
            item.status = "cancelada"
            continue
        try:
            item.provedor_id = _enviar(item)
            item.status = "enviada"
            item.enviado_em = agora_local()
            enviados += 1
        except Exception as erro:
            item.tentativas += 1
            item.ultimo_erro = type(erro).__name__
            if item.tentativas >= 3:
                item.status = "falhou"
    db.commit()
    return enviados


def _enviar(item: Notificacao) -> str:
    if os.getenv("NOTIFICACAO_PROVEDOR", "simulado") == "simulado":
        return f"simulado-{item.id}"
    cliente = item.agendamento.cliente_relacionado
    destino = f"+55{cliente.telefone}"
    origem = os.environ["TWILIO_FROM_NUMBER"]
    if item.canal == "whatsapp":
        destino, origem = f"whatsapp:{destino}", f"whatsapp:{origem}"
    api = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
    mensagem = api.messages.create(body=f"Olá, {cliente.nome}! Lembrete: seu agendamento com {item.agendamento.barbeiro.nome} é amanhã às {item.agendamento.horario.strftime('%H:%M')}.", from_=origem, to=destino)
    return mensagem.sid
