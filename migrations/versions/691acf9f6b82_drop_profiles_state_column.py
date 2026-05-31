"""drop profiles state column

Revision ID: 691acf9f6b82
Revises: e8bbef329343
Create Date: 2026-05-24 23:11:36.910505

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "691acf9f6b82"
down_revision: Union[str, Sequence[str], None] = "e8bbef329343"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("profiles", "state")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "profiles",
        sa.Column(
            "state",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
