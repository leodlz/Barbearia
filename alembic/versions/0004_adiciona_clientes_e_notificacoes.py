"""Adiciona clientes, sessão lógica e lembretes."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("clientes", sa.Column("id", sa.Integer(), nullable=False), sa.Column("nome", sa.String(100), nullable=False), sa.Column("telefone", sa.String(11), nullable=False), sa.Column("cpf", sa.String(11), nullable=False), sa.Column("criado_em", sa.DateTime(), nullable=False), sa.Column("atualizado_em", sa.DateTime(), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("cpf"))
    op.create_index("ix_clientes_id", "clientes", ["id"])
    op.create_index("ix_clientes_telefone", "clientes", ["telefone"])
    with op.batch_alter_table("agendamentos") as batch:
        batch.add_column(sa.Column("cliente_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_agendamentos_cliente_id", "clientes", ["cliente_id"], ["id"])
    op.create_table("notificacoes", sa.Column("id", sa.Integer(), nullable=False), sa.Column("agendamento_id", sa.Integer(), nullable=False), sa.Column("canal", sa.String(20), nullable=False), sa.Column("enviar_em", sa.DateTime(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("tentativas", sa.Integer(), nullable=False), sa.Column("enviado_em", sa.DateTime(), nullable=True), sa.Column("provedor_id", sa.String(), nullable=True), sa.Column("ultimo_erro", sa.String(), nullable=True), sa.ForeignKeyConstraint(["agendamento_id"], ["agendamentos.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("agendamento_id"))
    op.create_index("ix_notificacoes_id", "notificacoes", ["id"])
    op.create_index("ix_notificacoes_enviar_em", "notificacoes", ["enviar_em"])

def downgrade() -> None:
    op.drop_table("notificacoes")
    with op.batch_alter_table("agendamentos") as batch:
        batch.drop_constraint("fk_agendamentos_cliente_id", type_="foreignkey")
        batch.drop_column("cliente_id")
    op.drop_table("clientes")
