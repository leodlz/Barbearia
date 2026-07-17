import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from twilio.request_validator import RequestValidator

from app.database.connection import get_db
from app.models.notificacao import Notificacao


router = APIRouter(prefix="/api/notificacoes", tags=["Notificações"])


@router.post("/twilio/status", status_code=204)
async def status_twilio(request: Request, db: Session = Depends(get_db)) -> None:
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not token:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Callback Twilio não configurado.")
    formulario = dict(await request.form())
    assinatura = request.headers.get("X-Twilio-Signature", "")
    url_publica = os.getenv("TWILIO_STATUS_CALLBACK_URL", str(request.url))
    if not RequestValidator(token).validate(url_publica, formulario, assinatura):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Assinatura Twilio inválida.")

    provedor_id = formulario.get("MessageSid")
    notificacao = db.query(Notificacao).filter(Notificacao.provedor_id == provedor_id).first()
    if not notificacao:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificação não encontrada.")
    situacao = formulario.get("MessageStatus", "")
    if situacao == "delivered":
        notificacao.status = "entregue"
        notificacao.ultimo_erro = None
    elif situacao in ("failed", "undelivered"):
        notificacao.status = "falhou"
        notificacao.ultimo_erro = formulario.get("ErrorCode") or situacao
    elif situacao in ("accepted", "queued", "sending", "sent"):
        notificacao.status = "enviada"
    db.commit()
