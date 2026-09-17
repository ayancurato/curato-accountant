"""Add field column to AuditLog

Revision ID: f0f8559c3187
Revises: c5f6295c80ab
Create Date: 2026-09-17 08:46:00.511535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0f8559c3187'
down_revision: Union[str, Sequence[str], None] = 'c5f6295c80ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('audit_logs', sa.Column('field', sa.String(), nullable=True))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('audit_logs', 'field')
    # ### end Alembic commands ###
