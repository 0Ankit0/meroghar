"""Add RLS policies for bills and bill_allocations tables

Implements T093 from tasks.md.

Revision ID: 005_add_bills_rls_policies
Revises: 004_add_bills_tables
Create Date: 2025-10-27 10:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_bills_rls_policies'
down_revision: Union[str, None] = '004_add_bills_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS and create policies for bills tables."""
    
    # ==================== Enable RLS ====================
    
    op.execute('ALTER TABLE bills ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE bill_allocations ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE recurring_bills ENABLE ROW LEVEL SECURITY')
    
    # ==================== Bills Table Policies ====================
    
    # Policy: Owners can view bills for their properties
    op.execute("""
        CREATE POLICY bills_select_owner ON bills
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = bills.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Intermediaries can view bills for assigned properties
    op.execute("""
        CREATE POLICY bills_select_intermediary ON bills
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = bills.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Tenants can view bills allocated to them
    op.execute("""
        CREATE POLICY bills_select_tenant ON bills
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM bill_allocations
                JOIN tenants ON bill_allocations.tenant_id = tenants.id
                WHERE bill_allocations.bill_id = bills.id
                AND tenants.user_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Intermediaries can insert bills for assigned properties
    op.execute("""
        CREATE POLICY bills_insert_intermediary ON bills
        FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = bills.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Intermediaries can update bills for assigned properties
    op.execute("""
        CREATE POLICY bills_update_intermediary ON bills
        FOR UPDATE
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = bills.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Intermediaries can delete bills for assigned properties
    op.execute("""
        CREATE POLICY bills_delete_intermediary ON bills
        FOR DELETE
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = bills.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # ==================== Bill Allocations Table Policies ====================
    
    # Policy: Owners can view all allocations for their properties
    op.execute("""
        CREATE POLICY bill_allocations_select_owner ON bill_allocations
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM bills
                JOIN properties ON bills.property_id = properties.id
                WHERE bills.id = bill_allocations.bill_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Intermediaries can view allocations for assigned properties
    op.execute("""
        CREATE POLICY bill_allocations_select_intermediary ON bill_allocations
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM bills
                JOIN property_assignments ON bills.property_id = property_assignments.property_id
                WHERE bills.id = bill_allocations.bill_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Tenants can view their own allocations
    op.execute("""
        CREATE POLICY bill_allocations_select_tenant ON bill_allocations
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM tenants
                WHERE tenants.id = bill_allocations.tenant_id
                AND tenants.user_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Intermediaries can insert allocations for assigned properties
    op.execute("""
        CREATE POLICY bill_allocations_insert_intermediary ON bill_allocations
        FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM bills
                JOIN property_assignments ON bills.property_id = property_assignments.property_id
                WHERE bills.id = bill_allocations.bill_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Intermediaries can update allocations for assigned properties
    op.execute("""
        CREATE POLICY bill_allocations_update_intermediary ON bill_allocations
        FOR UPDATE
        USING (
            EXISTS (
                SELECT 1 FROM bills
                JOIN property_assignments ON bills.property_id = property_assignments.property_id
                WHERE bills.id = bill_allocations.bill_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Intermediaries can delete allocations for assigned properties
    op.execute("""
        CREATE POLICY bill_allocations_delete_intermediary ON bill_allocations
        FOR DELETE
        USING (
            EXISTS (
                SELECT 1 FROM bills
                JOIN property_assignments ON bills.property_id = property_assignments.property_id
                WHERE bills.id = bill_allocations.bill_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # ==================== Recurring Bills Table Policies ====================
    
    # Policy: Owners can view recurring bills for their properties
    op.execute("""
        CREATE POLICY recurring_bills_select_owner ON recurring_bills
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = recurring_bills.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Intermediaries can view recurring bills for assigned properties
    op.execute("""
        CREATE POLICY recurring_bills_select_intermediary ON recurring_bills
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = recurring_bills.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Intermediaries can insert recurring bills for assigned properties
    op.execute("""
        CREATE POLICY recurring_bills_insert_intermediary ON recurring_bills
        FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = recurring_bills.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Intermediaries can update recurring bills for assigned properties
    op.execute("""
        CREATE POLICY recurring_bills_update_intermediary ON recurring_bills
        FOR UPDATE
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = recurring_bills.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Intermediaries can delete recurring bills for assigned properties
    op.execute("""
        CREATE POLICY recurring_bills_delete_intermediary ON recurring_bills
        FOR DELETE
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = recurring_bills.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)


def downgrade() -> None:
    """Drop RLS policies and disable RLS for bills tables."""
    
    # Drop bills policies
    op.execute('DROP POLICY IF EXISTS bills_select_owner ON bills')
    op.execute('DROP POLICY IF EXISTS bills_select_intermediary ON bills')
    op.execute('DROP POLICY IF EXISTS bills_select_tenant ON bills')
    op.execute('DROP POLICY IF EXISTS bills_insert_intermediary ON bills')
    op.execute('DROP POLICY IF EXISTS bills_update_intermediary ON bills')
    op.execute('DROP POLICY IF EXISTS bills_delete_intermediary ON bills')
    
    # Drop bill_allocations policies
    op.execute('DROP POLICY IF EXISTS bill_allocations_select_owner ON bill_allocations')
    op.execute('DROP POLICY IF EXISTS bill_allocations_select_intermediary ON bill_allocations')
    op.execute('DROP POLICY IF EXISTS bill_allocations_select_tenant ON bill_allocations')
    op.execute('DROP POLICY IF EXISTS bill_allocations_insert_intermediary ON bill_allocations')
    op.execute('DROP POLICY IF EXISTS bill_allocations_update_intermediary ON bill_allocations')
    op.execute('DROP POLICY IF EXISTS bill_allocations_delete_intermediary ON bill_allocations')
    
    # Drop recurring_bills policies
    op.execute('DROP POLICY IF EXISTS recurring_bills_select_owner ON recurring_bills')
    op.execute('DROP POLICY IF EXISTS recurring_bills_select_intermediary ON recurring_bills')
    op.execute('DROP POLICY IF EXISTS recurring_bills_insert_intermediary ON recurring_bills')
    op.execute('DROP POLICY IF EXISTS recurring_bills_update_intermediary ON recurring_bills')
    op.execute('DROP POLICY IF EXISTS recurring_bills_delete_intermediary ON recurring_bills')
    
    # Disable RLS
    op.execute('ALTER TABLE bills DISABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE bill_allocations DISABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE recurring_bills DISABLE ROW LEVEL SECURITY')
