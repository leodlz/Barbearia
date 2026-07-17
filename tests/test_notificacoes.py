from datetime import date, datetime, time, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from twilio.request_validator import RequestValidator

from app.models.agendamento import Agendamento
from app.models.notificacao import Notificacao
from app.services import notificacao_service


def test_lembrete_confirmado_continua_ativo(client: TestClient, session_factory: sessionmaker[Session], monkeypatch) -> None:
    servico = client.post('/servicos', json={'nome': 'Corte', 'preco': '40.00', 'duracao_minutos': 30}).json()
    barbeiro = client.post('/barbeiros', json={'nome': 'Carlos'}).json()
    client.post(f"/barbeiros/{barbeiro['id']}/servicos/{servico['id']}")
    with session_factory() as db:
        agendamento = Agendamento(cliente='Cliente', barbeiro_id=barbeiro['id'], servico_id=servico['id'], data=date.today() + timedelta(days=1), horario=time(10), status='confirmado', preco_no_agendamento='40.00')
        db.add(agendamento)
        db.commit()
        db.add(Notificacao(agendamento_id=agendamento.id, canal='sms', enviar_em=datetime.now() - timedelta(minutes=1), status='pendente', tentativas=0))
        db.commit()
        monkeypatch.setattr(notificacao_service, '_enviar', lambda item: 'SM-confirmado')
        assert notificacao_service.processar_pendentes(db) == 1
        assert db.query(Notificacao).one().status == 'enviada'


def test_callback_twilio_valida_assinatura_e_registra_entrega(client: TestClient, session_factory: sessionmaker[Session], monkeypatch) -> None:
    token = 'token-de-teste'
    url = 'http://testserver/api/notificacoes/twilio/status'
    monkeypatch.setenv('TWILIO_AUTH_TOKEN', token)
    monkeypatch.setenv('TWILIO_STATUS_CALLBACK_URL', url)
    with session_factory() as db:
        db.add(Notificacao(agendamento_id=1, canal='sms', enviar_em=datetime.now(), status='enviada', tentativas=0, provedor_id='SM-teste'))
        db.commit()
    dados = {'MessageSid': 'SM-teste', 'MessageStatus': 'delivered'}
    assinatura = RequestValidator(token).compute_signature(url, dados)
    assert client.post('/api/notificacoes/twilio/status', data=dados, headers={'X-Twilio-Signature': assinatura}).status_code == 204
    with session_factory() as db:
        assert db.query(Notificacao).one().status == 'entregue'
    assert client.post('/api/notificacoes/twilio/status', data=dados, headers={'X-Twilio-Signature': 'invalida'}).status_code == 403
