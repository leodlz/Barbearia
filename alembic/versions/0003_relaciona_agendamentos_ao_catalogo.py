"""Relaciona agendamentos a barbeiros e serviços."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SERVICO_LEGADO = "Serviço legado (migração)"


def upgrade() -> None:
    op.add_column("agendamentos", sa.Column("barbeiro_id", sa.Integer(), nullable=True))
    op.add_column("agendamentos", sa.Column("servico_id", sa.Integer(), nullable=True))

    op.execute(
        sa.text(
            """
            INSERT INTO barbeiros (nome, ativo)
            SELECT DISTINCT a.barbeiro, 0
            FROM agendamentos AS a
            WHERE NOT EXISTS (
                SELECT 1 FROM barbeiros AS b WHERE b.nome = a.barbeiro
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO servicos (nome, descricao, preco, duracao_minutos, ativo)
            SELECT :nome, 'Criado para preservar agendamentos antigos', 0, 30, 0
            WHERE EXISTS (SELECT 1 FROM agendamentos)
              AND NOT EXISTS (SELECT 1 FROM servicos WHERE nome = :nome)
            """
        ).bindparams(nome=SERVICO_LEGADO)
    )
    op.execute(
        sa.text(
            """
            UPDATE agendamentos
            SET barbeiro_id = (
                SELECT b.id FROM barbeiros AS b
                WHERE b.nome = agendamentos.barbeiro
            ),
                servico_id = (
                SELECT s.id FROM servicos AS s WHERE s.nome = :nome
            )
            """
        ).bindparams(nome=SERVICO_LEGADO)
    )
    op.execute(
        sa.text(
            """
            INSERT OR IGNORE INTO barbeiros_servicos (barbeiro_id, servico_id)
            SELECT DISTINCT barbeiro_id, servico_id
            FROM agendamentos
            WHERE barbeiro_id IS NOT NULL AND servico_id IS NOT NULL
            """
        )
    )

    with op.batch_alter_table("agendamentos") as batch_op:
        batch_op.alter_column("barbeiro_id", nullable=False)
        batch_op.alter_column("servico_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_agendamentos_barbeiro_id",
            "barbeiros",
            ["barbeiro_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_agendamentos_servico_id",
            "servicos",
            ["servico_id"],
            ["id"],
        )
        batch_op.drop_column("barbeiro")


def downgrade() -> None:
    with op.batch_alter_table("agendamentos") as batch_op:
        batch_op.add_column(sa.Column("barbeiro", sa.String(), nullable=True))

    op.execute(
        """
        UPDATE agendamentos
        SET barbeiro = (
            SELECT b.nome FROM barbeiros AS b
            WHERE b.id = agendamentos.barbeiro_id
        )
        """
    )

    with op.batch_alter_table("agendamentos") as batch_op:
        batch_op.alter_column("barbeiro", nullable=False)
        batch_op.drop_constraint("fk_agendamentos_servico_id", type_="foreignkey")
        batch_op.drop_constraint("fk_agendamentos_barbeiro_id", type_="foreignkey")
        batch_op.drop_column("servico_id")
        batch_op.drop_column("barbeiro_id")
