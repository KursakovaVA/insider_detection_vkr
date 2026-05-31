"""add events rule_eval column

Revision ID: 9313ef727012
Revises: 691acf9f6b82
Create Date: 2026-05-27 10:25:49.377274

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9313ef727012"
down_revision: Union[str, Sequence[str], None] = "691acf9f6b82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "events",
        sa.Column(
            "rule_eval",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("events", "rule_eval")
