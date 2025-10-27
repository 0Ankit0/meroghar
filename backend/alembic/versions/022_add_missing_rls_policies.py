"""Add missing RLS policies for sync_logs, report_templates, generated_reports, payments, transactions

Revision ID: 022
Revises: 021
Create Date: 2025-10-27

Implements T261: Security audit - verify all RLS policies are correct
This migration adds RLS policies for tables that were missing them.
"""

from alembic import op


# revision identifiers, used by Alembic
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add RLS policies for missing tables."""
    
    # ========================================
    # 1. PAYMENTS TABLE RLS POLICIES
    # ========================================
    # Users can see payments for tenants they have access to
    
    op.execute("""
        -- Enable RLS on payments table
        ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
        
        -- Policy: Users can see payments for their accessible tenants
        DROP POLICY IF EXISTS payments_access_policy ON payments;
        CREATE POLICY payments_access_policy ON payments
            USING (
                tenant_id IN (
                    -- Tenant's own payments
                    SELECT id FROM tenants
                    WHERE user_id = current_setting('app.current_user_id')::uuid
                    
                    UNION
                    
                    -- Property owner's tenant payments
                    SELECT id FROM tenants
                    WHERE property_id IN (
                        SELECT id FROM properties
                        WHERE owner_id = current_setting('app.current_user_id')::uuid
                    )
                    
                    UNION
                    
                    -- Intermediary's assigned property tenant payments
                    SELECT id FROM tenants
                    WHERE property_id IN (
                        SELECT property_id FROM property_assignments
                        WHERE user_id = current_setting('app.current_user_id')::uuid
                    )
                )
            );
    """)
    
    # ========================================
    # 2. TRANSACTIONS TABLE RLS POLICIES
    # ========================================
    # Users can see transactions for payments they have access to
    
    op.execute("""
        -- Enable RLS on transactions table
        ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
        
        -- Policy: Users can see transactions for their accessible payments
        DROP POLICY IF EXISTS transactions_access_policy ON transactions;
        CREATE POLICY transactions_access_policy ON transactions
            USING (
                payment_id IN (
                    -- Get accessible payment IDs (reuse payments logic)
                    SELECT id FROM payments
                    WHERE tenant_id IN (
                        SELECT id FROM tenants
                        WHERE user_id = current_setting('app.current_user_id')::uuid
                        
                        UNION
                        
                        SELECT id FROM tenants
                        WHERE property_id IN (
                            SELECT id FROM properties
                            WHERE owner_id = current_setting('app.current_user_id')::uuid
                        )
                        
                        UNION
                        
                        SELECT id FROM tenants
                        WHERE property_id IN (
                            SELECT property_id FROM property_assignments
                            WHERE user_id = current_setting('app.current_user_id')::uuid
                        )
                    )
                )
            );
    """)
    
    # ========================================
    # 3. RECURRING BILLS TABLE RLS POLICIES
    # ========================================
    # Users can see recurring bills for properties they have access to
    
    op.execute("""
        -- Enable RLS on recurring_bills table
        ALTER TABLE recurring_bills ENABLE ROW LEVEL SECURITY;
        
        -- Policy: Users can see recurring bills for their accessible properties
        DROP POLICY IF EXISTS recurring_bills_access_policy ON recurring_bills;
        CREATE POLICY recurring_bills_access_policy ON recurring_bills
            USING (
                property_id IN (
                    -- Property owner's properties
                    SELECT id FROM properties
                    WHERE owner_id = current_setting('app.current_user_id')::uuid
                    
                    UNION
                    
                    -- Intermediary's assigned properties
                    SELECT property_id FROM property_assignments
                    WHERE user_id = current_setting('app.current_user_id')::uuid
                )
            );
    """)
    
    # ========================================
    # 4. SYNC LOGS TABLE RLS POLICIES
    # ========================================
    # Users can only see their own sync logs
    
    op.execute("""
        -- Enable RLS on sync_logs table
        ALTER TABLE sync_logs ENABLE ROW LEVEL SECURITY;
        
        -- Policy: Users can only see their own sync logs
        DROP POLICY IF EXISTS sync_logs_isolation_policy ON sync_logs;
        CREATE POLICY sync_logs_isolation_policy ON sync_logs
            USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    # ========================================
    # 5. REPORT TEMPLATES TABLE RLS POLICIES
    # ========================================
    # Users can see their own templates and system templates
    
    op.execute("""
        -- Enable RLS on report_templates table
        ALTER TABLE report_templates ENABLE ROW LEVEL SECURITY;
        
        -- Policy: Users can see their own templates and system templates
        DROP POLICY IF EXISTS report_templates_access_policy ON report_templates;
        CREATE POLICY report_templates_access_policy ON report_templates
            USING (
                created_by = current_setting('app.current_user_id')::uuid
                OR is_system = TRUE
            );
    """)
    
    # ========================================
    # 6. GENERATED REPORTS TABLE RLS POLICIES
    # ========================================
    # Users can see reports they generated or have access to via share token
    
    op.execute("""
        -- Enable RLS on generated_reports table
        ALTER TABLE generated_reports ENABLE ROW LEVEL SECURITY;
        
        -- Policy: Users can see their own reports
        -- Note: Share token access is handled at application level, not RLS
        DROP POLICY IF EXISTS generated_reports_access_policy ON generated_reports;
        CREATE POLICY generated_reports_access_policy ON generated_reports
            USING (
                generated_by = current_setting('app.current_user_id')::uuid
                OR template_id IN (
                    -- Reports from templates the user has access to
                    SELECT id FROM report_templates
                    WHERE created_by = current_setting('app.current_user_id')::uuid
                    OR is_system = TRUE
                )
            );
    """)


def downgrade() -> None:
    """Remove RLS policies."""
    
    # Drop all RLS policies created in this migration
    op.execute("""
        -- Drop payments RLS policies
        DROP POLICY IF EXISTS payments_access_policy ON payments;
        ALTER TABLE payments DISABLE ROW LEVEL SECURITY;
        
        -- Drop transactions RLS policies
        DROP POLICY IF EXISTS transactions_access_policy ON transactions;
        ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;
        
        -- Drop recurring_bills RLS policies
        DROP POLICY IF EXISTS recurring_bills_access_policy ON recurring_bills;
        ALTER TABLE recurring_bills DISABLE ROW LEVEL SECURITY;
        
        -- Drop sync_logs RLS policies
        DROP POLICY IF EXISTS sync_logs_isolation_policy ON sync_logs;
        ALTER TABLE sync_logs DISABLE ROW LEVEL SECURITY;
        
        -- Drop report_templates RLS policies
        DROP POLICY IF EXISTS report_templates_access_policy ON report_templates;
        ALTER TABLE report_templates DISABLE ROW LEVEL SECURITY;
        
        -- Drop generated_reports RLS policies
        DROP POLICY IF EXISTS generated_reports_access_policy ON generated_reports;
        ALTER TABLE generated_reports DISABLE ROW LEVEL SECURITY;
    """)
