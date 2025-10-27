"""Add sync_logs table for offline synchronization

Revision ID: 009
Revises: 008
Create Date: 2025-01-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create sync_logs table with enums and indexes."""
    
    # Create sync_status enum
    op.execute("""
        CREATE TYPE sync_status AS ENUM (
            'pending',
            'in_progress',
            'success',
            'failed',
            'conflict'
        )
    """)
    
    # Create sync_operation enum
    op.execute("""
        CREATE TYPE sync_operation AS ENUM (
            'create',
            'update',
            'delete',
            'bulk'
        )
    """)
    
    # Create sync_logs table
    op.create_table(
        'sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('device_name', sa.String(length=255), nullable=True),
        sa.Column('operation', sa.Enum(
            'create', 'update', 'delete', 'bulk',
            name='sync_operation',
            create_type=False
        ), nullable=False),
        sa.Column('status', sa.Enum(
            'pending', 'in_progress', 'success', 'failed', 'conflict',
            name='sync_status',
            create_type=False
        ), nullable=False, server_default='pending'),
        sa.Column('records_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_conflict', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('conflict_details', JSONB, nullable=True),
        sa.Column('sync_metadata', JSONB, nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient queries
    op.create_index(
        'ix_sync_logs_user_device',
        'sync_logs',
        ['user_id', 'device_id']
    )
    op.create_index(
        'ix_sync_logs_status_retry',
        'sync_logs',
        ['status', 'next_retry_at']
    )
    op.create_index(
        'ix_sync_logs_started_at',
        'sync_logs',
        ['started_at']
    )


def downgrade() -> None:
    """Drop sync_logs table and enums."""
    
    # Drop indexes
    op.drop_index('ix_sync_logs_started_at', table_name='sync_logs')
    op.drop_index('ix_sync_logs_status_retry', table_name='sync_logs')
    op.drop_index('ix_sync_logs_user_device', table_name='sync_logs')
    
    # Drop table
    op.drop_table('sync_logs')
    
    # Drop enums
    op.execute('DROP TYPE sync_operation')
    op.execute('DROP TYPE sync_status')
