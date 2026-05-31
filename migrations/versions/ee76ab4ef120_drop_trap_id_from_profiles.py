"""drop trap_id from profiles

Revision ID: ee76ab4ef120
Revises: 9313ef727012
Create Date: 2026-05-28 22:17:18.564207

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ee76ab4ef120"
down_revision: Union[str, Sequence[str], None] = "9313ef727012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TEMP TABLE profiles_agg AS
        SELECT
            src_ip,
            MAX(risk_score) AS risk_score,
            MAX(last_seen) AS last_seen
        FROM profiles
        GROUP BY src_ip;
        """
    )
    op.execute("DELETE FROM profiles;")
    op.drop_constraint("profiles_pkey", "profiles", type_="primary")
    op.drop_column("profiles", "trap_id")
    op.create_primary_key("profiles_pkey", "profiles", ["src_ip"])
    op.execute(
        """
        INSERT INTO profiles (src_ip, risk_score, last_seen)
        SELECT src_ip, risk_score, last_seen FROM profiles_agg;
        """
    )
    op.execute("DROP TABLE profiles_agg;")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "profiles",
        sa.Column(
            "trap_id",
            sa.String(length=64),
            nullable=False,
            server_default="core",
        ),
    )
    op.drop_constraint("profiles_pkey", "profiles", type_="primary")
    op.create_primary_key("profiles_pkey", "profiles", ["trap_id", "src_ip"])
