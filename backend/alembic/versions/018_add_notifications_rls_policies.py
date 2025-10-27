"""Add RLS policies for notifications table

Revision ID: 018
Revises: 017
Create Date: 2025-10-27 16:36:00.000000

Implements T252 from tasks.md (notification RLS policies).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '018'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add RLS policies for notifications table."""
    
    # Enable RLS on notifications table
    op.execute('ALTER TABLE notifications ENABLE ROW LEVEL SECURITY')
    
    # Policy 1: Users can view their own notifications
    op.execute("""
        CREATE POLICY notifications_select_own ON notifications
        FOR SELECT
        USING (user_id = current_setting('app.current_user_id')::uuid)
    """)
    
    # Policy 2: Users can update their own notifications (mark as read)
    op.execute("""
        CREATE POLICY notifications_update_own ON notifications
        FOR UPDATE
        USING (user_id = current_setting('app.current_user_id')::uuid)
        WITH CHECK (user_id = current_setting('app.current_user_id')::uuid)
    """)
    
    # Policy 3: System can insert notifications for any user
    # (Allows notification service to create notifications)
    op.execute("""
        CREATE POLICY notifications_insert_system ON notifications
        FOR INSERT
        WITH CHECK (true)
    """)
    
    # Policy 4: Users can delete their own notifications
    op.execute("""
        CREATE POLICY notifications_delete_own ON notifications
        FOR DELETE
        USING (user_id = current_setting('app.current_user_id')::uuid)
    """)


def downgrade() -> None:
    """Remove RLS policies from notifications table."""
    
    # Drop all policies
    op.execute('DROP POLICY IF EXISTS notifications_delete_own ON notifications')
    op.execute('DROP POLICY IF EXISTS notifications_insert_system ON notifications')
    op.execute('DROP POLICY IF EXISTS notifications_update_own ON notifications')
    op.execute('DROP POLICY IF EXISTS notifications_select_own ON notifications')
    
    # Disable RLS
    op.execute('ALTER TABLE notifications DISABLE ROW LEVEL SECURITY')
