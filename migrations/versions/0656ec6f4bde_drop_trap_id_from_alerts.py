"""drop trap_id from alerts

Revision ID: 0656ec6f4bde
Revises: ee76ab4ef120
Create Date: 2026-05-28 22:58:48.957066

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0656ec6f4bde"
down_revision: Union[str, Sequence[str], None] = "ee76ab4ef120"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("alerts", "trap_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "alerts",
        sa.Column(
            "trap_id",
            sa.String(length=64),
            nullable=False,
            server_default="core",
        ),
    )
