"""Add FCM token to users table

Revision ID: 017
Revises: 016
Create Date: 2025-10-27 16:31:00.000000

Implements T238 from tasks.md (FCM token storage).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '017'
down_revision: Union[str, None] = '016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add fcm_token column to users table."""
    op.add_column(
        'users',
        sa.Column(
            'fcm_token',
            sa.String(length=500),
            nullable=True,
            comment='Firebase Cloud Messaging device token for push notifications'
        )
    )
    
    # Create index for faster lookups
    op.create_index(
        'idx_users_fcm_token',
        'users',
        ['fcm_token'],
        unique=False,
        postgresql_where=sa.text("fcm_token IS NOT NULL")
    )


def downgrade() -> None:
    """Remove fcm_token column from users table."""
    op.drop_index('idx_users_fcm_token', table_name='users')
    op.drop_column('users', 'fcm_token')
