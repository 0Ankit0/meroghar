"""add notifications table

Revision ID: 016
Revises: 015
Create Date: 2025-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision: str = "016"
down_revision: Union[str, None] = "015"
branch_label: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notifications table and related enums."""
    # Create notification_type enum
    op.execute("""
        CREATE TYPE notification_type AS ENUM (
            'payment_received',
            'payment_overdue',
            'bill_created',
            'bill_allocated',
            'document_uploaded',
            'document_expiring',
            'rent_increment',
            'message_received',
            'expense_submitted',
            'expense_approved',
            'lease_expiring',
            'maintenance_scheduled',
            'system_announcement'
        )
    """)

    # Create notification_priority enum
    op.execute("""
        CREATE TYPE notification_priority AS ENUM (
            'low',
            'normal',
            'high',
            'urgent'
        )
    """)

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, comment="Notification identifier"),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Recipient user"),
        sa.Column("title", sa.String(200), nullable=False, comment="Notification title/heading"),
        sa.Column("body", sa.Text, nullable=False, comment="Notification message body"),
        sa.Column("notification_type", sa.Enum(name="notification_type"), nullable=False, comment="Type of notification"),
        sa.Column("priority", sa.Enum(name="notification_priority"), nullable=False, server_default="normal", comment="Notification priority level"),
        sa.Column("deep_link", sa.String(500), nullable=True, comment="Deep link for in-app navigation"),
        sa.Column("metadata", JSON, nullable=True, comment="Additional context data as JSON"),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false", comment="Read status"),
        sa.Column("read_at", sa.DateTime, nullable=True, comment="When notification was marked as read"),
        sa.Column("fcm_message_id", sa.String(200), nullable=True, comment="Firebase Cloud Messaging message ID"),
        sa.Column("sent_at", sa.DateTime, nullable=True, comment="When push notification was sent"),
        sa.Column("delivery_failed", sa.Boolean, nullable=False, server_default="false", comment="Whether delivery failed"),
        sa.Column("failure_reason", sa.Text, nullable=True, comment="Reason for delivery failure"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="Record creation timestamp"),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="Last update timestamp"),
    )

    # Create indexes
    op.create_index("ix_notifications_id", "notifications", ["id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_notification_type", "notifications", ["notification_type"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_index("ix_notifications_user_unread", "notifications", ["user_id", "is_read"])
    op.create_index("ix_notifications_user_type", "notifications", ["user_id", "notification_type"])
    op.create_index("ix_notifications_created_desc", "notifications", ["created_at"], postgresql_using="btree", postgresql_ops={"created_at": "DESC"})


def downgrade() -> None:
    """Drop notifications table and enums."""
    op.drop_index("ix_notifications_created_desc", "notifications")
    op.drop_index("ix_notifications_user_type", "notifications")
    op.drop_index("ix_notifications_user_unread", "notifications")
    op.drop_index("ix_notifications_created_at", "notifications")
    op.drop_index("ix_notifications_is_read", "notifications")
    op.drop_index("ix_notifications_notification_type", "notifications")
    op.drop_index("ix_notifications_user_id", "notifications")
    op.drop_index("ix_notifications_id", "notifications")
    
    op.drop_table("notifications")
    
    op.execute("DROP TYPE notification_priority")
    op.execute("DROP TYPE notification_type")
