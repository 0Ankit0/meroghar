"""add performance indexes

Revision ID: 021
Revises: 020
Create Date: 2025-01-29 18:12:00.000000

This migration adds database indexes to optimize query performance
across all frequently accessed tables.

Indexes are added for:
- Foreign key lookups
- Date range queries
- Status filters
- Composite queries

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for all tables"""
    
    # ====================
    # Users Table Indexes
    # ====================
    op.create_index(
        'idx_users_email',
        'users',
        ['email'],
        unique=True,
        if_not_exists=True
    )
    op.create_index(
        'idx_users_role',
        'users',
        ['role'],
        if_not_exists=True
    )
    op.create_index(
        'idx_users_is_active',
        'users',
        ['is_active'],
        if_not_exists=True
    )
    
    # ====================
    # Properties Table Indexes
    # ====================
    op.create_index(
        'idx_properties_owner_id',
        'properties',
        ['owner_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_properties_property_type',
        'properties',
        ['property_type'],
        if_not_exists=True
    )
    op.create_index(
        'idx_properties_created_at',
        'properties',
        [sa.text('created_at DESC')],
        if_not_exists=True
    )
    
    # ====================
    # Property Assignments Table Indexes
    # ====================
    op.create_index(
        'idx_property_assignments_property_id',
        'property_assignments',
        ['property_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_property_assignments_user_id',
        'property_assignments',
        ['user_id'],
        if_not_exists=True
    )
    # Composite index for finding assignments
    op.create_index(
        'idx_property_assignments_property_user',
        'property_assignments',
        ['property_id', 'user_id'],
        unique=True,
        if_not_exists=True
    )
    
    # ====================
    # Tenants Table Indexes
    # ====================
    op.create_index(
        'idx_tenants_property_id',
        'tenants',
        ['property_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_tenants_user_id',
        'tenants',
        ['user_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_tenants_status',
        'tenants',
        ['status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_tenants_billing_day',
        'tenants',
        ['billing_day'],
        if_not_exists=True
    )
    # Composite indexes for common queries
    op.create_index(
        'idx_tenants_property_status',
        'tenants',
        ['property_id', 'status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_tenants_unit_number',
        'tenants',
        ['property_id', 'unit_number'],
        if_not_exists=True
    )
    
    # ====================
    # Payments Table Indexes
    # ====================
    op.create_index(
        'idx_payments_tenant_id',
        'payments',
        ['tenant_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_payments_payment_date',
        'payments',
        [sa.text('payment_date DESC')],
        if_not_exists=True
    )
    op.create_index(
        'idx_payments_status',
        'payments',
        ['status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_payments_payment_method',
        'payments',
        ['payment_method'],
        if_not_exists=True
    )
    op.create_index(
        'idx_payments_created_at',
        'payments',
        [sa.text('created_at DESC')],
        if_not_exists=True
    )
    # Composite indexes for date range queries
    op.create_index(
        'idx_payments_tenant_date',
        'payments',
        ['tenant_id', sa.text('payment_date DESC')],
        if_not_exists=True
    )
    op.create_index(
        'idx_payments_tenant_status',
        'payments',
        ['tenant_id', 'status'],
        if_not_exists=True
    )
    # Index for analytics queries
    op.create_index(
        'idx_payments_date_status',
        'payments',
        [sa.text('payment_date DESC'), 'status'],
        if_not_exists=True
    )
    
    # ====================
    # Transactions Table Indexes
    # ====================
    op.create_index(
        'idx_transactions_payment_id',
        'transactions',
        ['payment_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_transactions_gateway',
        'transactions',
        ['gateway'],
        if_not_exists=True
    )
    op.create_index(
        'idx_transactions_status',
        'transactions',
        ['status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_transactions_transaction_id',
        'transactions',
        ['gateway_transaction_id'],
        if_not_exists=True
    )
    
    # ====================
    # Bills Table Indexes
    # ====================
    op.create_index(
        'idx_bills_property_id',
        'bills',
        ['property_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_bills_bill_type',
        'bills',
        ['bill_type'],
        if_not_exists=True
    )
    op.create_index(
        'idx_bills_status',
        'bills',
        ['status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_bills_due_date',
        'bills',
        [sa.text('due_date DESC')],
        if_not_exists=True
    )
    op.create_index(
        'idx_bills_billing_period_start',
        'bills',
        [sa.text('billing_period_start DESC')],
        if_not_exists=True
    )
    # Composite indexes
    op.create_index(
        'idx_bills_property_status',
        'bills',
        ['property_id', 'status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_bills_property_type',
        'bills',
        ['property_id', 'bill_type'],
        if_not_exists=True
    )
    
    # ====================
    # Bill Allocations Table Indexes
    # ====================
    op.create_index(
        'idx_bill_allocations_bill_id',
        'bill_allocations',
        ['bill_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_bill_allocations_tenant_id',
        'tenants',
        ['tenant_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_bill_allocations_status',
        'bill_allocations',
        ['status'],
        if_not_exists=True
    )
    # Composite index for tenant's bills
    op.create_index(
        'idx_bill_allocations_tenant_status',
        'bill_allocations',
        ['tenant_id', 'status'],
        if_not_exists=True
    )
    
    # ====================
    # Recurring Bills Table Indexes
    # ====================
    op.create_index(
        'idx_recurring_bills_property_id',
        'recurring_bills',
        ['property_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_recurring_bills_is_active',
        'recurring_bills',
        ['is_active'],
        if_not_exists=True
    )
    op.create_index(
        'idx_recurring_bills_next_generation',
        'recurring_bills',
        ['next_generation_date'],
        if_not_exists=True
    )
    # Composite for finding active recurring bills
    op.create_index(
        'idx_recurring_bills_active_next',
        'recurring_bills',
        ['is_active', 'next_generation_date'],
        if_not_exists=True
    )
    
    # ====================
    # Expenses Table Indexes
    # ====================
    op.create_index(
        'idx_expenses_property_id',
        'expenses',
        ['property_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_expenses_category',
        'expenses',
        ['category'],
        if_not_exists=True
    )
    op.create_index(
        'idx_expenses_status',
        'expenses',
        ['status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_expenses_expense_date',
        'expenses',
        [sa.text('expense_date DESC')],
        if_not_exists=True
    )
    op.create_index(
        'idx_expenses_created_by',
        'expenses',
        ['created_by'],
        if_not_exists=True
    )
    # Composite indexes
    op.create_index(
        'idx_expenses_property_date',
        'expenses',
        ['property_id', sa.text('expense_date DESC')],
        if_not_exists=True
    )
    op.create_index(
        'idx_expenses_property_category',
        'expenses',
        ['property_id', 'category'],
        if_not_exists=True
    )
    op.create_index(
        'idx_expenses_status_property',
        'expenses',
        ['status', 'property_id'],
        if_not_exists=True
    )
    
    # ====================
    # Documents Table Indexes
    # ====================
    op.create_index(
        'idx_documents_tenant_id',
        'documents',
        ['tenant_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_documents_property_id',
        'documents',
        ['property_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_documents_document_type',
        'documents',
        ['document_type'],
        if_not_exists=True
    )
    op.create_index(
        'idx_documents_expiration_date',
        'documents',
        ['expiration_date'],
        if_not_exists=True
    )
    op.create_index(
        'idx_documents_uploaded_by',
        'documents',
        ['uploaded_by'],
        if_not_exists=True
    )
    # Index for finding expiring documents
    op.create_index(
        'idx_documents_expiring_soon',
        'documents',
        ['expiration_date'],
        postgresql_where=sa.text("expiration_date IS NOT NULL AND expiration_date > CURRENT_DATE"),
        if_not_exists=True
    )
    
    # ====================
    # Messages Table Indexes
    # ====================
    op.create_index(
        'idx_messages_tenant_id',
        'messages',
        ['tenant_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_messages_sent_by',
        'messages',
        ['sent_by'],
        if_not_exists=True
    )
    op.create_index(
        'idx_messages_status',
        'messages',
        ['status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_messages_message_type',
        'messages',
        ['message_type'],
        if_not_exists=True
    )
    op.create_index(
        'idx_messages_sent_at',
        'messages',
        [sa.text('sent_at DESC')],
        if_not_exists=True
    )
    # Composite indexes
    op.create_index(
        'idx_messages_tenant_sent_at',
        'messages',
        ['tenant_id', sa.text('sent_at DESC')],
        if_not_exists=True
    )
    
    # ====================
    # Notifications Table Indexes
    # ====================
    op.create_index(
        'idx_notifications_user_id',
        'notifications',
        ['user_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_notifications_is_read',
        'notifications',
        ['is_read'],
        if_not_exists=True
    )
    op.create_index(
        'idx_notifications_notification_type',
        'notifications',
        ['notification_type'],
        if_not_exists=True
    )
    op.create_index(
        'idx_notifications_created_at',
        'notifications',
        [sa.text('created_at DESC')],
        if_not_exists=True
    )
    # Composite indexes for common queries
    op.create_index(
        'idx_notifications_user_read',
        'notifications',
        ['user_id', 'is_read'],
        if_not_exists=True
    )
    op.create_index(
        'idx_notifications_user_created',
        'notifications',
        ['user_id', sa.text('created_at DESC')],
        if_not_exists=True
    )
    # Partial index for unread notifications (most common query)
    op.create_index(
        'idx_notifications_unread',
        'notifications',
        ['user_id', sa.text('created_at DESC')],
        postgresql_where=sa.text("is_read = FALSE"),
        if_not_exists=True
    )
    
    # ====================
    # Sync Logs Table Indexes
    # ====================
    op.create_index(
        'idx_sync_logs_user_id',
        'sync_logs',
        ['user_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_sync_logs_device_id',
        'sync_logs',
        ['device_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_sync_logs_status',
        'sync_logs',
        ['status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_sync_logs_synced_at',
        'sync_logs',
        [sa.text('synced_at DESC')],
        if_not_exists=True
    )
    # Composite for finding user's sync history
    op.create_index(
        'idx_sync_logs_user_device_synced',
        'sync_logs',
        ['user_id', 'device_id', sa.text('synced_at DESC')],
        if_not_exists=True
    )
    
    # ====================
    # Report Templates Table Indexes
    # ====================
    op.create_index(
        'idx_report_templates_report_type',
        'report_templates',
        ['report_type'],
        if_not_exists=True
    )
    op.create_index(
        'idx_report_templates_created_by',
        'report_templates',
        ['created_by'],
        if_not_exists=True
    )
    op.create_index(
        'idx_report_templates_is_active',
        'report_templates',
        ['is_active'],
        if_not_exists=True
    )
    op.create_index(
        'idx_report_templates_is_system',
        'report_templates',
        ['is_system'],
        if_not_exists=True
    )
    # Composite for finding active templates
    op.create_index(
        'idx_report_templates_active_type',
        'report_templates',
        ['is_active', 'report_type'],
        if_not_exists=True
    )
    
    # ====================
    # Generated Reports Table Indexes
    # ====================
    op.create_index(
        'idx_generated_reports_template_id',
        'generated_reports',
        ['template_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_generated_reports_generated_by',
        'generated_reports',
        ['generated_by'],
        if_not_exists=True
    )
    op.create_index(
        'idx_generated_reports_report_type',
        'generated_reports',
        ['report_type'],
        if_not_exists=True
    )
    op.create_index(
        'idx_generated_reports_generated_at',
        'generated_reports',
        [sa.text('generated_at DESC')],
        if_not_exists=True
    )
    op.create_index(
        'idx_generated_reports_period_start',
        'generated_reports',
        [sa.text('period_start DESC')],
        if_not_exists=True
    )
    op.create_index(
        'idx_generated_reports_share_token',
        'generated_reports',
        ['share_token'],
        unique=True,
        postgresql_where=sa.text("share_token IS NOT NULL"),
        if_not_exists=True
    )
    # Composite for finding user's reports
    op.create_index(
        'idx_generated_reports_user_generated',
        'generated_reports',
        ['generated_by', sa.text('generated_at DESC')],
        if_not_exists=True
    )
    # Index for cleanup task (old reports)
    op.create_index(
        'idx_generated_reports_old',
        'generated_reports',
        ['generated_at'],
        postgresql_where=sa.text("generated_at < CURRENT_DATE - INTERVAL '90 days'"),
        if_not_exists=True
    )


def downgrade():
    """Drop all performance indexes"""
    
    # Generated Reports
    op.drop_index('idx_generated_reports_old', table_name='generated_reports', if_exists=True)
    op.drop_index('idx_generated_reports_user_generated', table_name='generated_reports', if_exists=True)
    op.drop_index('idx_generated_reports_share_token', table_name='generated_reports', if_exists=True)
    op.drop_index('idx_generated_reports_period_start', table_name='generated_reports', if_exists=True)
    op.drop_index('idx_generated_reports_generated_at', table_name='generated_reports', if_exists=True)
    op.drop_index('idx_generated_reports_report_type', table_name='generated_reports', if_exists=True)
    op.drop_index('idx_generated_reports_generated_by', table_name='generated_reports', if_exists=True)
    op.drop_index('idx_generated_reports_template_id', table_name='generated_reports', if_exists=True)
    
    # Report Templates
    op.drop_index('idx_report_templates_active_type', table_name='report_templates', if_exists=True)
    op.drop_index('idx_report_templates_is_system', table_name='report_templates', if_exists=True)
    op.drop_index('idx_report_templates_is_active', table_name='report_templates', if_exists=True)
    op.drop_index('idx_report_templates_created_by', table_name='report_templates', if_exists=True)
    op.drop_index('idx_report_templates_report_type', table_name='report_templates', if_exists=True)
    
    # Sync Logs
    op.drop_index('idx_sync_logs_user_device_synced', table_name='sync_logs', if_exists=True)
    op.drop_index('idx_sync_logs_synced_at', table_name='sync_logs', if_exists=True)
    op.drop_index('idx_sync_logs_status', table_name='sync_logs', if_exists=True)
    op.drop_index('idx_sync_logs_device_id', table_name='sync_logs', if_exists=True)
    op.drop_index('idx_sync_logs_user_id', table_name='sync_logs', if_exists=True)
    
    # Notifications
    op.drop_index('idx_notifications_unread', table_name='notifications', if_exists=True)
    op.drop_index('idx_notifications_user_created', table_name='notifications', if_exists=True)
    op.drop_index('idx_notifications_user_read', table_name='notifications', if_exists=True)
    op.drop_index('idx_notifications_created_at', table_name='notifications', if_exists=True)
    op.drop_index('idx_notifications_notification_type', table_name='notifications', if_exists=True)
    op.drop_index('idx_notifications_is_read', table_name='notifications', if_exists=True)
    op.drop_index('idx_notifications_user_id', table_name='notifications', if_exists=True)
    
    # Messages
    op.drop_index('idx_messages_tenant_sent_at', table_name='messages', if_exists=True)
    op.drop_index('idx_messages_sent_at', table_name='messages', if_exists=True)
    op.drop_index('idx_messages_message_type', table_name='messages', if_exists=True)
    op.drop_index('idx_messages_status', table_name='messages', if_exists=True)
    op.drop_index('idx_messages_sent_by', table_name='messages', if_exists=True)
    op.drop_index('idx_messages_tenant_id', table_name='messages', if_exists=True)
    
    # Documents
    op.drop_index('idx_documents_expiring_soon', table_name='documents', if_exists=True)
    op.drop_index('idx_documents_uploaded_by', table_name='documents', if_exists=True)
    op.drop_index('idx_documents_expiration_date', table_name='documents', if_exists=True)
    op.drop_index('idx_documents_document_type', table_name='documents', if_exists=True)
    op.drop_index('idx_documents_property_id', table_name='documents', if_exists=True)
    op.drop_index('idx_documents_tenant_id', table_name='documents', if_exists=True)
    
    # Expenses
    op.drop_index('idx_expenses_status_property', table_name='expenses', if_exists=True)
    op.drop_index('idx_expenses_property_category', table_name='expenses', if_exists=True)
    op.drop_index('idx_expenses_property_date', table_name='expenses', if_exists=True)
    op.drop_index('idx_expenses_created_by', table_name='expenses', if_exists=True)
    op.drop_index('idx_expenses_expense_date', table_name='expenses', if_exists=True)
    op.drop_index('idx_expenses_status', table_name='expenses', if_exists=True)
    op.drop_index('idx_expenses_category', table_name='expenses', if_exists=True)
    op.drop_index('idx_expenses_property_id', table_name='expenses', if_exists=True)
    
    # Recurring Bills
    op.drop_index('idx_recurring_bills_active_next', table_name='recurring_bills', if_exists=True)
    op.drop_index('idx_recurring_bills_next_generation', table_name='recurring_bills', if_exists=True)
    op.drop_index('idx_recurring_bills_is_active', table_name='recurring_bills', if_exists=True)
    op.drop_index('idx_recurring_bills_property_id', table_name='recurring_bills', if_exists=True)
    
    # Bill Allocations
    op.drop_index('idx_bill_allocations_tenant_status', table_name='bill_allocations', if_exists=True)
    op.drop_index('idx_bill_allocations_status', table_name='bill_allocations', if_exists=True)
    op.drop_index('idx_bill_allocations_tenant_id', table_name='bill_allocations', if_exists=True)
    op.drop_index('idx_bill_allocations_bill_id', table_name='bill_allocations', if_exists=True)
    
    # Bills
    op.drop_index('idx_bills_property_type', table_name='bills', if_exists=True)
    op.drop_index('idx_bills_property_status', table_name='bills', if_exists=True)
    op.drop_index('idx_bills_billing_period_start', table_name='bills', if_exists=True)
    op.drop_index('idx_bills_due_date', table_name='bills', if_exists=True)
    op.drop_index('idx_bills_status', table_name='bills', if_exists=True)
    op.drop_index('idx_bills_bill_type', table_name='bills', if_exists=True)
    op.drop_index('idx_bills_property_id', table_name='bills', if_exists=True)
    
    # Transactions
    op.drop_index('idx_transactions_transaction_id', table_name='transactions', if_exists=True)
    op.drop_index('idx_transactions_status', table_name='transactions', if_exists=True)
    op.drop_index('idx_transactions_gateway', table_name='transactions', if_exists=True)
    op.drop_index('idx_transactions_payment_id', table_name='transactions', if_exists=True)
    
    # Payments
    op.drop_index('idx_payments_date_status', table_name='payments', if_exists=True)
    op.drop_index('idx_payments_tenant_status', table_name='payments', if_exists=True)
    op.drop_index('idx_payments_tenant_date', table_name='payments', if_exists=True)
    op.drop_index('idx_payments_created_at', table_name='payments', if_exists=True)
    op.drop_index('idx_payments_payment_method', table_name='payments', if_exists=True)
    op.drop_index('idx_payments_status', table_name='payments', if_exists=True)
    op.drop_index('idx_payments_payment_date', table_name='payments', if_exists=True)
    op.drop_index('idx_payments_tenant_id', table_name='payments', if_exists=True)
    
    # Tenants
    op.drop_index('idx_tenants_unit_number', table_name='tenants', if_exists=True)
    op.drop_index('idx_tenants_property_status', table_name='tenants', if_exists=True)
    op.drop_index('idx_tenants_billing_day', table_name='tenants', if_exists=True)
    op.drop_index('idx_tenants_status', table_name='tenants', if_exists=True)
    op.drop_index('idx_tenants_user_id', table_name='tenants', if_exists=True)
    op.drop_index('idx_tenants_property_id', table_name='tenants', if_exists=True)
    
    # Property Assignments
    op.drop_index('idx_property_assignments_property_user', table_name='property_assignments', if_exists=True)
    op.drop_index('idx_property_assignments_user_id', table_name='property_assignments', if_exists=True)
    op.drop_index('idx_property_assignments_property_id', table_name='property_assignments', if_exists=True)
    
    # Properties
    op.drop_index('idx_properties_created_at', table_name='properties', if_exists=True)
    op.drop_index('idx_properties_property_type', table_name='properties', if_exists=True)
    op.drop_index('idx_properties_owner_id', table_name='properties', if_exists=True)
    
    # Users
    op.drop_index('idx_users_is_active', table_name='users', if_exists=True)
    op.drop_index('idx_users_role', table_name='users', if_exists=True)
    op.drop_index('idx_users_email', table_name='users', if_exists=True)
