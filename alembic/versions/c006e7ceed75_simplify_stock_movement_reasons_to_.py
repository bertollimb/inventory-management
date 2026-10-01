"""simplify stock movement reasons to purchase and use

Revision ID: <mantenha o que foi gerado>
Revises: a50d2df2c3e2
Create Date: <mantenha o que foi gerado>

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "<mantenha o que foi gerado>"
down_revision: Union[str, Sequence[str], None] = "a50d2df2c3e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_VALUES = ("PURCHASE", "SALE", "ADJUSTMENT", "RETURN")
NEW_VALUES = ("PURCHASE", "USE")


def upgrade() -> None:
    op.execute("ALTER TYPE movement_reason RENAME TO movement_reason_old")

    new_enum = postgresql.ENUM(*NEW_VALUES, name="movement_reason")
    new_enum.create(op.get_bind())

    # Existing test rows: map by movement direction, not by the old reason
    # value -- IN becomes PURCHASE, OUT becomes USE, regardless of what the
    # row previously said. There is no production data at this point.
    op.execute(
        """
        ALTER TABLE stock_movements
        ALTER COLUMN reason TYPE movement_reason
        USING (
            CASE movement_type::text
                WHEN 'IN' THEN 'PURCHASE'
                ELSE 'USE'
            END
        )::movement_reason
        """
    )

    op.execute("DROP TYPE movement_reason_old")


def downgrade() -> None:
    op.execute("ALTER TYPE movement_reason RENAME TO movement_reason_new")

    old_enum = postgresql.ENUM(*OLD_VALUES, name="movement_reason")
    old_enum.create(op.get_bind())

    op.execute(
        "ALTER TABLE stock_movements "
        "ALTER COLUMN reason TYPE movement_reason "
        "USING reason::text::movement_reason"
    )

    op.execute("DROP TYPE movement_reason_new")