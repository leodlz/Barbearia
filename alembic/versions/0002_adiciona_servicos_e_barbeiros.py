"""Adiciona serviços, barbeiros e suas associações."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "barbeiros",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_index(op.f("ix_barbeiros_id"), "barbeiros", ["id"], unique=False)

    op.create_table(
        "servicos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("descricao", sa.String(), nullable=True),
        sa.Column("preco", sa.Numeric(10, 2), nullable=False),
        sa.Column("duracao_minutos", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_index(op.f("ix_servicos_id"), "servicos", ["id"], unique=False)

    op.create_table(
        "barbeiros_servicos",
        sa.Column("barbeiro_id", sa.Integer(), nullable=False),
        sa.Column("servico_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["barbeiro_id"], ["barbeiros.id"]),
        sa.ForeignKeyConstraint(["servico_id"], ["servicos.id"]),
        sa.PrimaryKeyConstraint("barbeiro_id", "servico_id"),
    )


def downgrade() -> None:
    op.drop_table("barbeiros_servicos")
    op.drop_index(op.f("ix_servicos_id"), table_name="servicos")
    op.drop_table("servicos")
    op.drop_index(op.f("ix_barbeiros_id"), table_name="barbeiros")
    op.drop_table("barbeiros")
