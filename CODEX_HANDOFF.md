# CODEX HANDOFF

## Estado da entrega

Este documento registra o estado do projeto após a implementação do acesso de
clientes, lembretes, autenticação master, histórico do cliente, gestão
administrativa inicial e snapshot de preço. O escopo foi congelado antes de
novas expansões.

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

Banco local verificado em `0006 (head)`. Os snapshots dos registros anteriores
foram preenchidos com o preço atual disponível na migração.

## Variáveis de ambiente

```text
DATABASE_URL=sqlite:///./barbearia.db
SESSION_SECRET=
SESSION_HTTPS_ONLY=false
MASTER_NAME=
MASTER_USER=
MASTER_PASSWORD=
NOTIFICACAO_PROVEDOR=simulado|twilio
NOTIFICACAO_CANAL=sms|whatsapp
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
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

- Passando: **31**.
- Falhando: **0**.
- Banco de testes: SQLite em memória; não usa `barbearia.db`.
- Alembic: `0006 (head)` e `alembic check` sem operações pendentes.
- Dependências: `pip check` sem pacotes quebrados.

## Bugs e limitações conhecidas

- A interface master é funcional, porém inicial: os filtros existem na API,
  mas ainda não possuem todos os controles visuais.
- As APIs permitem editar serviços e barbeiros; a interface atual prioriza
  criação e ativação/desativação e ainda precisa refinar edição/associações.
- Não existe recuperação ou troca de senha pela interface.
- O master inicial deve trocar sua credencial por processo administrativo; não
  há tela de rotação ainda.
- Datas são comparadas com o relógio local sem timezone persistido.
- O worker de lembretes precisa rodar em processo separado; a entrega depende
  da fila do provedor.
- Concorrência extrema ainda depende da verificação transacional da aplicação,
  sem constraint de intervalo no banco.
- Registros legados sem `cliente_id` não podem ser reivindicados pelo cliente.
- O painel não implementa paginação para grandes volumes.

## Trabalho inacabado

- Refinar controles visuais de filtro e edição no painel master.
- Adicionar troca/recuperação de senha e rotação do master.
- Criar fluxo administrativo para vincular agendamentos legados a clientes.
- Adicionar paginação e ordenação configurável.
- Cobrir o JavaScript com testes de navegador/E2E.
- Configurar OTP e callbacks de entrega do Twilio.

## Próximos passos recomendados

1. Trocar imediatamente a senha inicial do master e implementar rotação segura.
2. Completar edição visual de serviços, barbeiros e associações usando as APIs
   já existentes.
3. Adicionar controles visuais para os filtros administrativos.
4. Criar testes E2E do cliente e master em navegador real.
5. Configurar timezone explícito da barbearia.
6. Configurar processo separado e monitorado para lembretes.
7. Só depois considerar recuperação de senha, OTP e paginação.

## Commits mais recentes

```text
a08d328 add client history and master interfaces
265c80b add master access and management APIs
acf94fb add cpf and password authentication
ed7bb52 improve mobile client booking flow
0202d44 add client identification and reminders
c70a359 document and prepare application deployment
1640b68 add appointment web interface
7c68db7 add appointment availability
69680d1 add service duration conflict detection
7d99a7a add barbers and services
```

O commit deste próprio documento será posterior aos hashes acima. Consulte
`git log --oneline` para a lista definitiva.
