"""Add updated_at to property_assignments for sync

Revision ID: 010
Revises: 009
Create Date: 2025-01-26 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add updated_at column to property_assignments table."""
    
    op.add_column(
        'property_assignments',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()')
        )
    )


def downgrade() -> None:
    """Remove updated_at column from property_assignments table."""
    
    op.drop_column('property_assignments', 'updated_at')
