"""Adiciona master, snapshot de preço e metadados."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("usuarios_master", sa.Column("id", sa.Integer(), nullable=False), sa.Column("nome", sa.String(100), nullable=False), sa.Column("usuario", sa.String(50), nullable=False), sa.Column("senha_hash", sa.String(), nullable=False), sa.Column("papel", sa.String(20), nullable=False), sa.Column("ativo", sa.Boolean(), nullable=False), sa.Column("criado_em", sa.DateTime(), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("usuario"))
    op.create_index("ix_usuarios_master_id", "usuarios_master", ["id"])
    agora = sa.func.current_timestamp()
    op.add_column("agendamentos", sa.Column("preco_no_agendamento", sa.Numeric(10,2), nullable=True))
    op.add_column("agendamentos", sa.Column("criado_em", sa.DateTime(), nullable=True))
    op.execute("UPDATE agendamentos SET preco_no_agendamento=(SELECT preco FROM servicos WHERE servicos.id=agendamentos.servico_id), criado_em=CURRENT_TIMESTAMP")
    with op.batch_alter_table("agendamentos") as batch:
        batch.alter_column("preco_no_agendamento", nullable=False)
        batch.alter_column("criado_em", nullable=False)
    op.add_column("servicos", sa.Column("criado_em", sa.DateTime(), nullable=True))
    op.add_column("servicos", sa.Column("atualizado_em", sa.DateTime(), nullable=True))
    op.execute("UPDATE servicos SET criado_em=CURRENT_TIMESTAMP, atualizado_em=CURRENT_TIMESTAMP")
    with op.batch_alter_table("servicos") as batch:
        batch.alter_column("criado_em", nullable=False); batch.alter_column("atualizado_em", nullable=False)
    op.add_column("barbeiros", sa.Column("descricao", sa.String(), nullable=True))
    op.add_column("barbeiros", sa.Column("criado_em", sa.DateTime(), nullable=True))
    op.add_column("barbeiros", sa.Column("atualizado_em", sa.DateTime(), nullable=True))
    op.execute("UPDATE barbeiros SET criado_em=CURRENT_TIMESTAMP, atualizado_em=CURRENT_TIMESTAMP")
    with op.batch_alter_table("barbeiros") as batch:
        batch.alter_column("criado_em", nullable=False); batch.alter_column("atualizado_em", nullable=False)

def downgrade() -> None:
    with op.batch_alter_table("barbeiros") as batch:
        batch.drop_column("atualizado_em"); batch.drop_column("criado_em"); batch.drop_column("descricao")
    with op.batch_alter_table("servicos") as batch:
        batch.drop_column("atualizado_em"); batch.drop_column("criado_em")
    with op.batch_alter_table("agendamentos") as batch:
        batch.drop_column("criado_em"); batch.drop_column("preco_no_agendamento")
    op.drop_table("usuarios_master")
