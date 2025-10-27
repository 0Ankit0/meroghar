"""Add messages table for bulk reminders

Revision ID: 011
Revises: 010
Create Date: 2025-01-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create messages table with enums and indexes."""
    
    # Create message_channel enum
    op.execute("""
        CREATE TYPE message_channel AS ENUM (
            'sms',
            'whatsapp',
            'email'
        )
    """)
    
    # Create message_status enum
    op.execute("""
        CREATE TYPE message_status AS ENUM (
            'pending',
            'scheduled',
            'sending',
            'sent',
            'delivered',
            'failed',
            'cancelled'
        )
    """)
    
    # Create message_template enum
    op.execute("""
        CREATE TYPE message_template AS ENUM (
            'payment_reminder',
            'payment_overdue',
            'payment_received',
            'lease_expiring',
            'maintenance_notice',
            'custom'
        )
    """)
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('sent_by', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('template', sa.Enum(
            'payment_reminder', 'payment_overdue', 'payment_received',
            'lease_expiring', 'maintenance_notice', 'custom',
            name='message_template',
            create_type=False
        ), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('channel', sa.Enum(
            'sms', 'whatsapp', 'email',
            name='message_channel',
            create_type=False
        ), nullable=False),
        sa.Column('recipient_phone', sa.String(length=20), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum(
            'pending', 'scheduled', 'sending', 'sent', 'delivered', 'failed', 'cancelled',
            name='message_status',
            create_type=False
        ), nullable=False, server_default='pending'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('provider_response', JSONB, nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('bulk_message_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sent_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient queries
    op.create_index('ix_messages_tenant_id', 'messages', ['tenant_id'])
    op.create_index('ix_messages_sent_by', 'messages', ['sent_by'])
    op.create_index('ix_messages_property_id', 'messages', ['property_id'])
    op.create_index('ix_messages_provider_message_id', 'messages', ['provider_message_id'])
    op.create_index('ix_messages_bulk_message_id', 'messages', ['bulk_message_id'])
    op.create_index('ix_messages_status_scheduled', 'messages', ['status', 'scheduled_at'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])


def downgrade() -> None:
    """Drop messages table and enums."""
    
    # Drop indexes
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_status_scheduled', table_name='messages')
    op.drop_index('ix_messages_bulk_message_id', table_name='messages')
    op.drop_index('ix_messages_provider_message_id', table_name='messages')
    op.drop_index('ix_messages_property_id', table_name='messages')
    op.drop_index('ix_messages_sent_by', table_name='messages')
    op.drop_index('ix_messages_tenant_id', table_name='messages')
    
    # Drop table
    op.drop_table('messages')
    
    # Drop enums
    op.execute('DROP TYPE message_template')
    op.execute('DROP TYPE message_status')
    op.execute('DROP TYPE message_channel')
