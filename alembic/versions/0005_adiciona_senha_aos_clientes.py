"""Adiciona hash de senha aos clientes."""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("clientes", sa.Column("senha_hash", sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column("clientes", "senha_hash")
