"""Add RLS policies for users, properties, and tenants tables

Implements T050-T052 from tasks.md.

Revision ID: 002_add_rls_policies
Revises: 001_initial_schema
Create Date: 2025-10-27 08:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_rls_policies'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS and create policies for users, properties, and tenants tables."""
    
    # ==================== Enable RLS ====================
    
    # Enable RLS on users table
    op.execute('ALTER TABLE users ENABLE ROW LEVEL SECURITY')
    
    # Enable RLS on properties table
    op.execute('ALTER TABLE properties ENABLE ROW LEVEL SECURITY')
    
    # Enable RLS on property_assignments table
    op.execute('ALTER TABLE property_assignments ENABLE ROW LEVEL SECURITY')
    
    # Enable RLS on tenants table
    op.execute('ALTER TABLE tenants ENABLE ROW LEVEL SECURITY')
    
    # ==================== Users Table Policies (T050) ====================
    
    # Policy: Users can view their own record
    op.execute("""
        CREATE POLICY users_select_own ON users
        FOR SELECT
        USING (id::text = current_setting('app.current_user_id', true))
    """)
    
    # Policy: Owners can view all users for their properties
    op.execute("""
        CREATE POLICY users_select_owner ON users
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Intermediaries can view tenant users for their assigned properties
    op.execute("""
        CREATE POLICY users_select_intermediary ON users
        FOR SELECT
        USING (
            role = 'tenant' AND
            EXISTS (
                SELECT 1 FROM tenants
                JOIN property_assignments ON tenants.property_id = property_assignments.property_id
                WHERE tenants.user_id = users.id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Intermediaries can insert tenant users
    op.execute("""
        CREATE POLICY users_insert_intermediary ON users
        FOR INSERT
        WITH CHECK (
            role = 'tenant' AND
            EXISTS (
                SELECT 1 FROM users creator
                WHERE creator.id::text = current_setting('app.current_user_id', true)
                AND creator.role = 'intermediary'
            )
        )
    """)
    
    # Policy: Users can update their own record
    op.execute("""
        CREATE POLICY users_update_own ON users
        FOR UPDATE
        USING (id::text = current_setting('app.current_user_id', true))
    """)
    
    # ==================== Properties Table Policies (T051) ====================
    
    # Policy: Owners can view their own properties
    op.execute("""
        CREATE POLICY properties_select_owner ON properties
        FOR SELECT
        USING (owner_id::text = current_setting('app.current_user_id', true))
    """)
    
    # Policy: Intermediaries can view assigned properties
    op.execute("""
        CREATE POLICY properties_select_intermediary ON properties
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = properties.id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Tenants can view their property
    op.execute("""
        CREATE POLICY properties_select_tenant ON properties
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM tenants
                WHERE tenants.property_id = properties.id
                AND tenants.user_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Owners can insert their own properties
    op.execute("""
        CREATE POLICY properties_insert_owner ON properties
        FOR INSERT
        WITH CHECK (owner_id::text = current_setting('app.current_user_id', true))
    """)
    
    # Policy: Owners can update their own properties
    op.execute("""
        CREATE POLICY properties_update_owner ON properties
        FOR UPDATE
        USING (owner_id::text = current_setting('app.current_user_id', true))
    """)
    
    # Policy: Owners can delete their own properties
    op.execute("""
        CREATE POLICY properties_delete_owner ON properties
        FOR DELETE
        USING (owner_id::text = current_setting('app.current_user_id', true))
    """)
    
    # ==================== Property Assignments Policies ====================
    
    # Policy: Owners can view assignments for their properties
    op.execute("""
        CREATE POLICY property_assignments_select_owner ON property_assignments
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = property_assignments.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Intermediaries can view their own assignments
    op.execute("""
        CREATE POLICY property_assignments_select_intermediary ON property_assignments
        FOR SELECT
        USING (intermediary_id::text = current_setting('app.current_user_id', true))
    """)
    
    # Policy: Owners can create assignments for their properties
    op.execute("""
        CREATE POLICY property_assignments_insert_owner ON property_assignments
        FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = property_assignments.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Owners can update assignments for their properties
    op.execute("""
        CREATE POLICY property_assignments_update_owner ON property_assignments
        FOR UPDATE
        USING (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = property_assignments.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # ==================== Tenants Table Policies (T052) ====================
    
    # Policy: Owners can view tenants for their properties
    op.execute("""
        CREATE POLICY tenants_select_owner ON tenants
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = tenants.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)
    
    # Policy: Intermediaries can view tenants for assigned properties
    op.execute("""
        CREATE POLICY tenants_select_intermediary ON tenants
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = tenants.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Tenants can view their own record
    op.execute("""
        CREATE POLICY tenants_select_own ON tenants
        FOR SELECT
        USING (user_id::text = current_setting('app.current_user_id', true))
    """)
    
    # Policy: Intermediaries can insert tenants for assigned properties
    op.execute("""
        CREATE POLICY tenants_insert_intermediary ON tenants
        FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = tenants.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Intermediaries can update tenants for assigned properties
    op.execute("""
        CREATE POLICY tenants_update_intermediary ON tenants
        FOR UPDATE
        USING (
            EXISTS (
                SELECT 1 FROM property_assignments
                WHERE property_assignments.property_id = tenants.property_id
                AND property_assignments.intermediary_id::text = current_setting('app.current_user_id', true)
                AND property_assignments.is_active = true
            )
        )
    """)
    
    # Policy: Owners can update tenants for their properties
    op.execute("""
        CREATE POLICY tenants_update_owner ON tenants
        FOR UPDATE
        USING (
            EXISTS (
                SELECT 1 FROM properties
                WHERE properties.id = tenants.property_id
                AND properties.owner_id::text = current_setting('app.current_user_id', true)
            )
        )
    """)


def downgrade() -> None:
    """Remove RLS policies and disable RLS."""
    
    # ==================== Drop Tenants Policies ====================
    op.execute('DROP POLICY IF EXISTS tenants_select_owner ON tenants')
    op.execute('DROP POLICY IF EXISTS tenants_select_intermediary ON tenants')
    op.execute('DROP POLICY IF EXISTS tenants_select_own ON tenants')
    op.execute('DROP POLICY IF EXISTS tenants_insert_intermediary ON tenants')
    op.execute('DROP POLICY IF EXISTS tenants_update_intermediary ON tenants')
    op.execute('DROP POLICY IF EXISTS tenants_update_owner ON tenants')
    
    # ==================== Drop Property Assignments Policies ====================
    op.execute('DROP POLICY IF EXISTS property_assignments_select_owner ON property_assignments')
    op.execute('DROP POLICY IF EXISTS property_assignments_select_intermediary ON property_assignments')
    op.execute('DROP POLICY IF EXISTS property_assignments_insert_owner ON property_assignments')
    op.execute('DROP POLICY IF EXISTS property_assignments_update_owner ON property_assignments')
    
    # ==================== Drop Properties Policies ====================
    op.execute('DROP POLICY IF EXISTS properties_select_owner ON properties')
    op.execute('DROP POLICY IF EXISTS properties_select_intermediary ON properties')
    op.execute('DROP POLICY IF EXISTS properties_select_tenant ON properties')
    op.execute('DROP POLICY IF EXISTS properties_insert_owner ON properties')
    op.execute('DROP POLICY IF EXISTS properties_update_owner ON properties')
    op.execute('DROP POLICY IF EXISTS properties_delete_owner ON properties')
    
    # ==================== Drop Users Policies ====================
    op.execute('DROP POLICY IF EXISTS users_select_own ON users')
    op.execute('DROP POLICY IF EXISTS users_select_owner ON users')
    op.execute('DROP POLICY IF EXISTS users_select_intermediary ON users')
    op.execute('DROP POLICY IF EXISTS users_insert_intermediary ON users')
    op.execute('DROP POLICY IF EXISTS users_update_own ON users')
    
    # ==================== Disable RLS ====================
    op.execute('ALTER TABLE tenants DISABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE property_assignments DISABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE properties DISABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE users DISABLE ROW LEVEL SECURITY')
