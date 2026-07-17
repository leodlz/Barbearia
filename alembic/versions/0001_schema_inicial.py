"""Cria o schema inicial de agendamentos."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agendamentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente", sa.String(), nullable=False),
        sa.Column("barbeiro", sa.String(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("horario", sa.Time(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agendamentos_id"),
        "agendamentos",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_agendamentos_id"), table_name="agendamentos")
    op.drop_table("agendamentos")
