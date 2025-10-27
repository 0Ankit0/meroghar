"""Add RLS policies for expenses table

Implements T140 from tasks.md.

Revision ID: 008_add_expenses_rls_policies
Revises: 007_add_expenses_table
Create Date: 2025-10-27 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008_add_expenses_rls_policies'
down_revision: Union[str, None] = '007_add_expenses_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS and create policies for expenses table."""
    
    # ==================== Enable RLS ====================
    
    # Enable RLS on expenses table
    op.execute('ALTER TABLE expenses ENABLE ROW LEVEL SECURITY')
    
    # ==================== Expenses Table Policies (T140) ====================
    
    # Policy: Intermediaries can view expenses for properties they manage
    op.execute("""
        CREATE POLICY expenses_select_intermediary ON expenses
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = expenses.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Owners can view expenses for properties they own
    op.execute("""
        CREATE POLICY expenses_select_owner ON expenses
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = expenses.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Intermediaries can insert expenses for properties they manage
    op.execute("""
        CREATE POLICY expenses_insert_intermediary ON expenses
        FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = expenses.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
            AND recorded_by::text = current_setting('app.current_user_id', true)
        )
    """)
    
    # Policy: Intermediaries can update expenses they recorded
    op.execute("""
        CREATE POLICY expenses_update_intermediary ON expenses
        FOR UPDATE
        USING (
            recorded_by::text = current_setting('app.current_user_id', true)
            AND status = 'pending'
            AND EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = expenses.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
        WITH CHECK (
            recorded_by::text = current_setting('app.current_user_id', true)
            AND status = 'pending'
        )
    """)
    
    # Policy: Owners can update (approve/reject/reimburse) expenses for their properties
    op.execute("""
        CREATE POLICY expenses_update_owner ON expenses
        FOR UPDATE
        USING (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = expenses.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = expenses.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
            AND (
                -- Allow status changes and approval fields
                status IN ('pending', 'approved', 'rejected', 'reimbursed')
            )
        )
    """)
    
    # Policy: Intermediaries can delete pending expenses they recorded
    op.execute("""
        CREATE POLICY expenses_delete_intermediary ON expenses
        FOR DELETE
        USING (
            recorded_by::text = current_setting('app.current_user_id', true)
            AND status = 'pending'
            AND EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = expenses.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)


def downgrade() -> None:
    """Drop RLS policies and disable RLS for expenses table."""
    
    # Drop policies
    op.execute('DROP POLICY IF EXISTS expenses_select_intermediary ON expenses')
    op.execute('DROP POLICY IF EXISTS expenses_select_owner ON expenses')
    op.execute('DROP POLICY IF EXISTS expenses_insert_intermediary ON expenses')
    op.execute('DROP POLICY IF EXISTS expenses_update_intermediary ON expenses')
    op.execute('DROP POLICY IF EXISTS expenses_update_owner ON expenses')
    op.execute('DROP POLICY IF EXISTS expenses_delete_intermediary ON expenses')
    
    # Disable RLS
    op.execute('ALTER TABLE expenses DISABLE ROW LEVEL SECURITY')
