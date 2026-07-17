"""Adiciona recuperação de senha dos clientes."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("recuperacoes_senha", sa.Column("id", sa.Integer(), nullable=False), sa.Column("cliente_id", sa.Integer(), nullable=False), sa.Column("codigo_hash", sa.String(), nullable=False), sa.Column("expira_em", sa.DateTime(), nullable=False), sa.Column("tentativas", sa.Integer(), nullable=False), sa.Column("usado_em", sa.DateTime(), nullable=True), sa.Column("criado_em", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_recuperacoes_senha_id", "recuperacoes_senha", ["id"])
    op.create_index("ix_recuperacoes_senha_cliente_id", "recuperacoes_senha", ["cliente_id"])

def downgrade() -> None:
    op.drop_table("recuperacoes_senha")
