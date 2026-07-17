# CODEX HANDOFF

## Estado da entrega

Este documento registra o estado do projeto após a implementação do acesso de
clientes, lembretes, autenticação master, histórico do cliente, gestão
administrativa, snapshot de preço, rotação de senha master, vínculo de
agendamentos legados e paginação da agenda.

## Arquitetura atual

```text
FastAPI route
  -> dependency de autenticação/autorização
  -> service com regras de negócio
  -> model SQLAlchemy
  -> SQLite
```

- `app/main.py`: composição da aplicação, sessão e arquivos estáticos.
- `app/routes/`: APIs públicas, de cliente e master.
- `app/dependencies/auth.py`: `require_cliente` e `require_master`.
- `app/services/`: regras, transações, disponibilidade e notificações.
- `app/models/`: entidades SQLAlchemy e relacionamentos.
- `app/schemas/`: contratos Pydantic.
- `app/static/`: páginas HTML/CSS/JavaScript sem framework.
- `alembic/`: histórico de migrações.
- `tests/`: testes com SQLite em memória.
- `scripts/create_master.py`: seed explícito e idempotente do master.

## Funcionalidades implementadas

### Clientes

- registro com nome, telefone, CPF e senha;
- CPF normalizado e validado;
- telefone normalizado;
- senha com hash `scrypt` e salt individual;
- login por CPF e senha;
- sessão assinada contendo somente `cliente_id`;
- logout;
- criação de agendamentos vinculados ao cliente;
- página e API de “Meus agendamentos”;
- consulta limitada aos agendamentos do cliente da sessão;
- cancelamento de agendamento próprio e futuro;
- lembrete persistente por SMS ou WhatsApp via Twilio ou provedor simulado.
- recuperação de senha por código temporário enviado ao telefone, com hash,
  expiração, intervalo entre solicitações e limite de tentativas;

### Master

- entidade `UsuarioMaster` separada de `Cliente`;
- login por usuário e senha com sessão `master_id`;
- `401` sem autenticação e `403` para papel incorreto;
- seed idempotente por variáveis de ambiente;
- dashboard com contagens úteis;
- listagem administrativa de agendamentos;
- filtros de backend por data, barbeiro, serviço, status e cliente/telefone;
- transições controladas de status;
- criação, edição, ativação e desativação de serviços;
- criação, edição, ativação e desativação de barbeiros;
- associação muitos-para-muitos entre barbeiros e serviços;
- aviso quantitativo de agendamentos futuros na desativação;
- páginas iniciais `/admin/login` e `/admin`.
- troca segura de senha com confirmação da senha atual;
- filtros visuais de agendamentos por data, catálogo, status e cliente;
- ordenação e paginação da agenda administrativa;
- edição visual de serviços, barbeiros e respectivas associações;
- busca de clientes por nome/telefone e vínculo de agendamentos legados, sem
  expor CPF.

### Agendamentos e catálogo

- disponibilidade por expediente, intervalo e duração;
- detecção de sobreposição;
- bloqueio de serviço/barbeiro inativo;
- status `agendado`, `confirmado`, `cancelado`, `concluido` e `faltou`;
- preço histórico em `preco_no_agendamento`;
- registros cancelados preservados e horários liberados;
- serviços e barbeiros desativados preservados no histórico.

## Modelos e relacionamentos

- `Cliente`: nome, telefone, CPF único, hash da senha e datas. Possui vários
  agendamentos.
- `UsuarioMaster`: nome, usuário único, hash da senha, papel `master`, ativo e
  data de criação.
- `Agendamento`: cliente textual legado, `cliente_id` opcional, `barbeiro_id`,
  `servico_id`, data, horário, status, snapshot de preço e criação.
- `Servico`: nome, descrição, preço `Numeric(10,2)`, duração, ativo e datas.
- `Barbeiro`: nome, descrição, ativo e datas.
- `barbeiros_servicos`: associação muitos-para-muitos.
- `Notificacao`: um lembrete por agendamento, canal, instante, tentativas,
  situação e identificador do provedor.
- `RecuperacaoSenha`: cliente, hash do código, expiração, tentativas, uso e
  criação. Vários pedidos podem existir, mas somente o mais recente válido é
  aceito.

Agendamentos legados podem ter `cliente_id = NULL`; eles permanecem disponíveis
para o master, mas não aparecem em “Meus agendamentos”.

## Autenticação

### Cliente

1. `POST /api/clientes/registro` ou `POST /api/clientes/login`.
2. Cookie de sessão assinado recebe somente `cliente_id`.
3. `require_cliente` consulta o cliente no banco em cada rota protegida.

### Master

1. Executar explicitamente `python scripts/create_master.py` com variáveis.
2. `POST /api/admin/login` cria sessão contendo somente `master_id`.
3. `require_master` verifica existência, atividade e papel no backend.
4. `PUT /api/admin/senha` exige a senha atual, confirmação da nova senha e gera
   um novo hash com salt sem encerrar a sessão válida.

Senhas, CPF e tokens não são retornados por schemas públicos.

## Regras importantes

- CPF deve ter 11 dígitos válidos e não repetidos.
- Senhas nunca são armazenadas em texto puro.
- Cliente nunca informa `cliente_id` para provar propriedade.
- Agendamento novo deve estar no futuro.
- Serviço e barbeiro precisam estar ativos e associados.
- `agendado -> confirmado|cancelado|concluido|faltou`.
- `confirmado -> cancelado|concluido|faltou`.
- Estados finais não podem ser reativados.
- Cancelamento não apaga o registro e libera o intervalo.
- Alterar preço de serviço não altera `preco_no_agendamento`.
- Desativar catálogo preserva histórico e compromissos futuros.
- Nenhuma desativação cancela automaticamente agendamentos.

## Migrações aplicadas

- `0001`: agendamentos iniciais.
- `0002`: serviços, barbeiros e associações.
- `0003`: relaciona agendamentos ao catálogo.
- `0004`: clientes e notificações.
- `0005`: hash de senha dos clientes.
- `0006`: usuário master, snapshot de preço e metadados.
- `0007`: códigos temporários de recuperação de senha dos clientes.

Banco local verificado em `0007 (head)`. Os snapshots dos registros anteriores
foram preenchidos com o preço atual disponível na migração.

## Variáveis de ambiente

```text
DATABASE_URL=sqlite:///./barbearia.db
SESSION_SECRET=
SESSION_HTTPS_ONLY=false
BARBEARIA_TIMEZONE=America/Sao_Paulo
MASTER_NAME=
MASTER_USER=
MASTER_PASSWORD=
NOTIFICACAO_PROVEDOR=simulado|twilio
NOTIFICACAO_CANAL=sms|whatsapp
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
TWILIO_STATUS_CALLBACK_URL=
```

`.env` e bancos `*.db` são ignorados. `.env.example` contém somente exemplos
sem segredos.

## Comandos

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
python scripts/create_master.py
fastapi dev app/main.py
python -m app.workers.lembretes
python -m pytest -q
```

- cliente: `http://127.0.0.1:8000/acesso`
- agendamento: `http://127.0.0.1:8000/agendar`
- histórico: `http://127.0.0.1:8000/meus-agendamentos`
- master: `http://127.0.0.1:8000/admin/login`
- OpenAPI: `http://127.0.0.1:8000/docs`

## Testes

- Passando: **39**.
- Falhando: **0**.
- Banco de testes: SQLite em memória; não usa `barbearia.db`.
- Alembic: `0007 (head)` e `alembic check` sem operações pendentes.
- Dependências: `pip check` sem pacotes quebrados.

## Bugs e limitações conhecidas

- Clientes recuperam a senha pelo telefone. O master usa troca autenticada na
  seção Segurança; recuperação externa do master não existe porque seu modelo
  não possui telefone ou e-mail verificado.
- Horários civis continuam armazenados sem `tzinfo`; as comparações usam o fuso
  IANA configurado em `BARBEARIA_TIMEZONE`, adequado para uma única unidade.
- O worker de lembretes precisa rodar em processo separado; o callback assinado
  registra o resultado informado pelo Twilio, mas a disponibilidade ainda
  depende da fila do provedor.
- Concorrência extrema ainda depende da verificação transacional da aplicação,
  sem constraint de intervalo no banco.
- O vínculo de registros legados depende de decisão manual do master e, por
  segurança, não permite reatribuição depois de concluído.
- O painel pagina a agenda, mas as telas de catálogo ainda carregam todos os
  serviços e barbeiros de uma vez.

## Trabalho inacabado

- Definir um canal verificado para eventual recuperação externa do master.
- Avaliar paginação das telas de catálogo quando o volume justificar.
- Cobrir o JavaScript com testes de navegador/E2E.
- Configurar OTP; o callback de entrega do Twilio já está implementado.

## Próximos passos recomendados

1. Usar a seção Segurança para trocar imediatamente a senha inicial do master.
2. Criar testes E2E do cliente e master em navegador real.
3. Configurar processo separado e monitorado para lembretes.
4. Publicar e cadastrar `TWILIO_STATUS_CALLBACK_URL`, então validar callbacks em
   uma conta Twilio de teste.
5. Configurar OTP apenas depois de definir o provedor e disponibilizar
   credenciais de ambiente de teste.
6. Definir telefone ou e-mail verificado antes de implementar recuperação
   externa do master.

## Commits mais recentes

```text
9aee83c add client password recovery
077713e track Twilio reminder delivery
b4ea7e5 configure barbershop timezone
f7692d0 add legacy linking and agenda pagination
ce5357a complete master management controls
f86b998 remove sensitive-looking test literals
6fd8812 document architecture and remaining work
a08d328 add client history and master interfaces
265c80b add master access and management APIs
acf94fb add cpf and password authentication
ed7bb52 improve mobile client booking flow
0202d44 add client identification and reminders
c70a359 document and prepare application deployment
```
