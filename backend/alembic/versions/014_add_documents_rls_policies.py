"""add documents rls policies

Revision ID: 014
Revises: 013
Create Date: 2025-10-27
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "014"
down_revision: Union[str, None] = "013"
branch_label: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Row Level Security policies for documents table."""
    # Enable RLS on documents table
    op.execute("ALTER TABLE documents ENABLE ROW LEVEL SECURITY;")

    # Policy: Uploader can select/update/delete their documents
    op.execute('''
        CREATE POLICY documents_uploader_select_update_delete ON documents
        FOR ALL
        TO authenticated
        USING (
            uploaded_by = auth.uid()
        )
        WITH CHECK (
            uploaded_by = auth.uid()
        );
    ''')

    # Policy: Tenant user can select documents belonging to their tenant
    op.execute('''
        CREATE POLICY documents_tenant_select ON documents
        FOR SELECT
        TO authenticated
        USING (
            tenant_id IN (
                SELECT id FROM tenants WHERE user_id = auth.uid()
            )
        );
    ''')

    # Policy: Property owner or intermediary can select documents for their properties
    op.execute('''
        CREATE POLICY documents_property_select ON documents
        FOR SELECT
        TO authenticated
        USING (
            property_id IN (
                SELECT id FROM properties
                WHERE owner_id = auth.uid() OR managed_by = auth.uid()
            )
        );
    ''')

    # Policy: System/admin role may see documents where uploaded_by IS NULL (if applicable)
    op.execute('''
        CREATE POLICY documents_system_select ON documents
        FOR SELECT
        TO authenticated
        USING (
            uploaded_by IS NULL
            AND (
                -- Allow tenant recipients
                tenant_id IN (
                    SELECT id FROM tenants WHERE user_id = auth.uid()
                )
                OR
                -- Allow owners/managers for property-scoped system documents
                property_id IN (
                    SELECT id FROM properties WHERE owner_id = auth.uid() OR managed_by = auth.uid()
                )
            )
        );
    ''')


def downgrade() -> None:
    """Remove Row Level Security policies for documents table."""
    op.execute("DROP POLICY IF EXISTS documents_system_select ON documents;")
    op.execute("DROP POLICY IF EXISTS documents_property_select ON documents;")
    op.execute("DROP POLICY IF EXISTS documents_tenant_select ON documents;")
    op.execute("DROP POLICY IF EXISTS documents_uploader_select_update_delete ON documents;")

    # Disable RLS
    op.execute("ALTER TABLE documents DISABLE ROW LEVEL SECURITY;")
