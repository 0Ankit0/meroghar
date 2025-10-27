"""add messages rls policies

Revision ID: 012
Revises: 011
Create Date: 2025-01-26
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: Union[str, None] = "011"
branch_label: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Add Row Level Security policies for messages table."""
    # Enable RLS on messages table
    op.execute("ALTER TABLE messages ENABLE ROW LEVEL SECURITY;")

    # Policy 1: Intermediaries can view messages they sent
    op.execute("""
        CREATE POLICY messages_intermediary_select ON messages
        FOR SELECT
        TO authenticated
        USING (
            sent_by = auth.uid()
            AND EXISTS (
                SELECT 1 FROM users
                WHERE users.id = auth.uid()
                AND users.role = 'intermediary'
            )
        );
    """)

    # Policy 2: Intermediaries can insert messages for their managed properties
    op.execute("""
        CREATE POLICY messages_intermediary_insert ON messages
        FOR INSERT
        TO authenticated
        WITH CHECK (
            sent_by = auth.uid()
            AND EXISTS (
                SELECT 1 FROM users
                WHERE users.id = auth.uid()
                AND users.role = 'intermediary'
            )
            AND (
                -- Check if property belongs to intermediary
                property_id IN (
                    SELECT id FROM properties
                    WHERE managed_by = auth.uid()
                )
                OR
                -- Check if tenant belongs to intermediary's property
                tenant_id IN (
                    SELECT t.id FROM tenants t
                    INNER JOIN properties p ON p.id = t.property_id
                    WHERE p.managed_by = auth.uid()
                )
            )
        );
    """)

    # Policy 3: Intermediaries can update messages they sent (e.g., cancel)
    op.execute("""
        CREATE POLICY messages_intermediary_update ON messages
        FOR UPDATE
        TO authenticated
        USING (
            sent_by = auth.uid()
            AND EXISTS (
                SELECT 1 FROM users
                WHERE users.id = auth.uid()
                AND users.role = 'intermediary'
            )
        );
    """)

    # Policy 4: Owners can view messages for their properties
    op.execute("""
        CREATE POLICY messages_owner_select ON messages
        FOR SELECT
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM users
                WHERE users.id = auth.uid()
                AND users.role = 'owner'
            )
            AND property_id IN (
                SELECT id FROM properties
                WHERE owner_id = auth.uid()
            )
        );
    """)

    # Policy 5: Tenants can view messages sent to them
    op.execute("""
        CREATE POLICY messages_tenant_select ON messages
        FOR SELECT
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM users
                WHERE users.id = auth.uid()
                AND users.role = 'tenant'
            )
            AND tenant_id IN (
                SELECT id FROM tenants
                WHERE user_id = auth.uid()
            )
        );
    """)

    # Policy 6: System-generated messages (sent_by IS NULL) are visible to recipients
    op.execute("""
        CREATE POLICY messages_system_select ON messages
        FOR SELECT
        TO authenticated
        USING (
            sent_by IS NULL
            AND (
                -- Tenant can see their own system messages
                tenant_id IN (
                    SELECT id FROM tenants
                    WHERE user_id = auth.uid()
                )
                OR
                -- Owner can see system messages for their properties
                (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE users.id = auth.uid()
                        AND users.role = 'owner'
                    )
                    AND property_id IN (
                        SELECT id FROM properties
                        WHERE owner_id = auth.uid()
                    )
                )
                OR
                -- Intermediary can see system messages for their managed properties
                (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE users.id = auth.uid()
                        AND users.role = 'intermediary'
                    )
                    AND property_id IN (
                        SELECT id FROM properties
                        WHERE managed_by = auth.uid()
                    )
                )
            )
        );
    """)


def downgrade() -> None:
    """Remove Row Level Security policies for messages table."""
    # Drop policies
    op.execute("DROP POLICY IF EXISTS messages_system_select ON messages;")
    op.execute("DROP POLICY IF EXISTS messages_tenant_select ON messages;")
    op.execute("DROP POLICY IF EXISTS messages_owner_select ON messages;")
    op.execute("DROP POLICY IF EXISTS messages_intermediary_update ON messages;")
    op.execute("DROP POLICY IF EXISTS messages_intermediary_insert ON messages;")
    op.execute("DROP POLICY IF EXISTS messages_intermediary_select ON messages;")

    # Disable RLS
    op.execute("ALTER TABLE messages DISABLE ROW LEVEL SECURITY;")
