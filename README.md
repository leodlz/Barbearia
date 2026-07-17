# Gerenciador de Barbearia

API e interface web para administrar serviços, barbeiros, disponibilidade e o
ciclo de vida de agendamentos de uma barbearia.

## Funcionalidades

- criação, listagem e consulta de agendamentos;
- cancelamento sem excluir o histórico;
- conclusão e registro de falta;
- bloqueio de agendamentos no passado;
- conflito por intervalo, barbeiro e duração do serviço;
- cadastro de serviços com preço decimal e duração;
- cadastro de barbeiros e associação muitos-para-muitos com serviços;
- consulta de horários disponíveis;
- interface de agendamento em `/web`;
- documentação OpenAPI em `/docs`;
- migrações Alembic e testes isolados com Pytest.

## Tecnologias

Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, SQLite, Alembic, Pytest,
HTML, CSS e JavaScript.

## Arquitetura

```text
requisição HTTP
  -> route (entrada e resposta HTTP)
  -> service (regras de negócio e transação)
  -> model SQLAlchemy
  -> banco de dados
```

```text
app/
├── database/       conexão e sessões
├── models/         tabelas e relacionamentos
├── routes/         endpoints FastAPI
├── schemas/        contratos Pydantic
├── services/       regras de negócio
├── static/         interface web
└── main.py          composição da aplicação
alembic/             migrações de banco
tests/               testes automatizados isolados
```

## Instalação no Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
```

O comando `alembic upgrade head` cria um banco novo ou aplica somente as
migrações que ainda faltam. Ele deve ser executado sempre que o projeto receber
uma nova migração.

## Execução

```powershell
fastapi dev app/main.py
```

- API: <http://127.0.0.1:8000>
- Swagger: <http://127.0.0.1:8000/docs>
- interface: <http://127.0.0.1:8000/web>

Antes de usar a interface, cadastre ao menos um serviço e um barbeiro pela
documentação `/docs` e associe os dois.

## Testes

```powershell
python -m pytest -q
```

Os testes usam SQLite em memória e nunca acessam `barbearia.db`.

## Endpoints principais

| Método | Caminho | Finalidade |
|---|---|---|
| `POST` | `/agendamentos` | Criar agendamento |
| `GET` | `/agendamentos` | Listar agendamentos |
| `GET` | `/agendamentos/{id}` | Consultar por ID |
| `PATCH` | `/agendamentos/{id}/cancelar` | Cancelar |
| `PATCH` | `/agendamentos/{id}/concluir` | Concluir |
| `PATCH` | `/agendamentos/{id}/falta` | Registrar falta |
| `GET` | `/disponibilidade` | Consultar horários livres |
| `POST/GET` | `/servicos` | Criar ou listar serviços |
| `GET` | `/servicos/{id}` | Consultar serviço |
| `POST/GET` | `/barbeiros` | Criar ou listar barbeiros |
| `GET` | `/barbeiros/{id}` | Consultar barbeiro |
| `POST/DELETE` | `/barbeiros/{id}/servicos/{servico_id}` | Alterar associação |

Consulte `/docs` para parâmetros, exemplos e schemas completos.

## Regras de negócio

- um novo agendamento começa com status `agendado`;
- o cliente não escolhe o status inicial;
- somente agendamentos futuros podem ser criados;
- somente barbeiros e serviços ativos podem ser agendados;
- o barbeiro precisa realizar o serviço escolhido;
- intervalos ocupados consideram a duração do serviço;
- `cancelado`, `concluido` e `faltou` são estados finais;
- cancelar preserva o registro e libera o horário imediatamente;
- cancelamento só é permitido antes do horário marcado;
- conclusão e falta só são permitidas depois do horário marcado;
- expediente do MVP: segunda a sábado, das 09:00 às 18:00;
- intervalo do MVP: 12:00 às 13:00;
- novos inícios são oferecidos a cada 30 minutos.

### Fuso horário

Defina `BARBEARIA_TIMEZONE` com um identificador IANA, como
`America/Sao_Paulo`. As regras de agendamento, disponibilidade, dashboard e
lembretes usam esse fuso mesmo que o servidor esteja configurado em outra
região. O schema atual ainda persiste horários civis sem `tzinfo`, adequado para
uma única unidade da barbearia.

## Banco de dados e migrações

O arquivo local `barbearia.db` é ignorado pelo Git. `create_all()` não é usado
para evoluir tabelas, porque ele não altera colunas existentes. Para criar uma
migração após mudar os models:

```powershell
alembic revision --autogenerate -m "descreve a mudança"
alembic upgrade head
```

Revise sempre o arquivo gerado antes de aplicar a migração.

## Configuração e implantação

### Acesso do cliente e lembretes

O cliente registra nome, telefone, CPF e senha em `/acesso`. Nos próximos
acessos, usa CPF e senha. A senha é armazenada como hash `scrypt` com salt; o
cookie assinado guarda somente o `cliente_id`.

O link “Esqueci minha senha” envia um código de seis dígitos pelo canal de
notificação configurado. O código é armazenado somente como hash, expira em 10
minutos e é bloqueado após cinco erros. No provedor `simulado`, o código aparece
na própria interface exclusivamente para desenvolvimento local.

Clientes acessam o histórico em `/meus-agendamentos`; a API sempre usa o
`cliente_id` da sessão e nunca aceita outro cliente como prova de propriedade.

O painel master fica em `/admin/login`. Para criar o primeiro usuário, defina
`MASTER_NAME`, `MASTER_USER` e `MASTER_PASSWORD` e execute:

```powershell
python scripts/create_master.py
```

O comando é idempotente: não recria o usuário nem sobrescreve sua senha. Rotas
administrativas validam a sessão master no backend; sessões de clientes recebem
`403` e visitantes sem sessão recebem `401`.

Agendamentos guardam `preco_no_agendamento`. Portanto, alterar o preço atual de
um serviço não modifica valores históricos. Serviços e barbeiros são
desativados, não apagados; compromissos futuros são preservados e apresentados
ao master para revisão manual.

Copie `.env.example` para configurar a sessão e o envio. Por padrão, lembretes
são simulados. Para envio real, defina `NOTIFICACAO_PROVEDOR=twilio`, escolha
`NOTIFICACAO_CANAL=sms` ou `whatsapp` e configure as credenciais Twilio. Execute
o worker em processo separado:

```powershell
python -m app.workers.lembretes
```

O worker procura lembretes vencidos a cada 30 segundos, evita reenvio após
sucesso e ignora agendamentos cancelados. Agendamentos confirmados continuam
elegíveis. Para acompanhar entrega real, configure `TWILIO_STATUS_CALLBACK_URL`
com a URL pública `/api/notificacoes/twilio/status` cadastrada no Twilio; o
endpoint valida a assinatura do provedor antes de atualizar o status. CPF nunca
é enviado nem registrado nas notificações.

Por padrão, a aplicação usa:

```text
DATABASE_URL=sqlite:///./barbearia.db
```

Outro banco pode ser informado pela variável de ambiente `DATABASE_URL`. O
repositório inclui um `Dockerfile`:

```powershell
docker build -t gerenciador-barbearia .
docker run --rm -p 8000:8000 gerenciador-barbearia
```

Em produção, use um volume persistente para SQLite ou configure um banco
gerenciado. Nenhum segredo deve ser commitado no repositório.
