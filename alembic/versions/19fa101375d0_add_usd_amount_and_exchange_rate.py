"""Add usd_amount and exchange_rate

Revision ID: 19fa101375d0
Revises: f0f8559c3187
Create Date: 2026-09-17 12:24:14.114176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19fa101375d0'
down_revision: Union[str, Sequence[str], None] = 'f0f8559c3187'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('transactions', sa.Column('usd_amount', sa.Numeric(), nullable=True))
    op.add_column('transactions', sa.Column('exchange_rate', sa.Numeric(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transactions', 'exchange_rate')
    op.drop_column('transactions', 'usd_amount')
