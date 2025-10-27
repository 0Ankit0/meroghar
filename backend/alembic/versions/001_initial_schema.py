"""Initial schema - User Story 1 models

Revision ID: 001
Revises: 
Create Date: 2025-01-27 07:55:00.000000

Creates tables for User Story 1:
- users (with role enum)
- properties
- property_assignments (junction table)
- tenants (with status enum)
- payments (stub for relationships)
- bill_allocations (stub for relationships)

Implements T028 from tasks.md.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema for User Story 1."""
    
    # Create enums
    op.execute("CREATE TYPE user_role AS ENUM ('owner', 'intermediary', 'tenant')")
    op.execute("CREATE TYPE tenant_status AS ENUM ('active', 'inactive', 'pending_move_out')")
    op.execute("CREATE TYPE payment_method AS ENUM ('cash', 'bank_transfer', 'online', 'upi', 'card', 'other')")
    op.execute("CREATE TYPE payment_type AS ENUM ('rent', 'security_deposit', 'bill_share', 'penalty', 'other')")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), comment='Unique user identifier'),
        sa.Column('email', sa.String(255), nullable=False, unique=True, comment='User email address (unique login)'),
        sa.Column('phone', sa.String(20), nullable=True, comment='Contact phone number (E.164 format)'),
        sa.Column('password_hash', sa.String(255), nullable=False, comment='bcrypt hashed password'),
        sa.Column('full_name', sa.String(255), nullable=False, comment="User's full name"),
        sa.Column('role', postgresql.ENUM('owner', 'intermediary', 'tenant', name='user_role'), nullable=False, comment='User role (immutable after creation)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment='Account active status'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Account creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Last update timestamp'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='Last login timestamp'),
    )
    
    # Indexes for users
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_active', 'users', ['is_active'], postgresql_where=sa.text('is_active = true'))
    
    # Create properties table
    op.create_table(
        'properties',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), comment='Unique property identifier'),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False, comment="Property owner (must be role='owner')"),
        sa.Column('name', sa.String(255), nullable=False, comment='Property name/identifier'),
        sa.Column('address_line1', sa.String(255), nullable=False, comment='Street address'),
        sa.Column('address_line2', sa.String(255), nullable=True, comment='Apartment/unit number'),
        sa.Column('city', sa.String(100), nullable=False, comment='City'),
        sa.Column('state', sa.String(100), nullable=False, comment='State/province'),
        sa.Column('postal_code', sa.String(20), nullable=False, comment='Postal/ZIP code'),
        sa.Column('country', sa.String(100), nullable=False, comment='Country'),
        sa.Column('total_units', sa.Integer(), nullable=False, comment='Number of rental units'),
        sa.Column('base_currency', sa.String(3), nullable=False, comment='ISO 4217 currency code (immutable after creation)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Property creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Last update timestamp'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('total_units > 0', name='check_total_units_positive'),
    )
    
    # Indexes for properties
    op.create_index('idx_properties_owner', 'properties', ['owner_id'])
    op.create_index('idx_properties_city', 'properties', ['city', 'state'])
    
    # Create property_assignments table
    op.create_table(
        'property_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), comment='Assignment identifier'),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Assigned property'),
        sa.Column('intermediary_id', postgresql.UUID(as_uuid=True), nullable=False, comment="Assigned intermediary (must be role='intermediary')"),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=False, comment='Owner who made assignment'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment='Active assignment flag'),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Assignment timestamp'),
        sa.Column('removed_at', sa.DateTime(), nullable=True, comment='Removal timestamp (soft delete)'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['intermediary_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('property_id', 'intermediary_id', 'is_active', name='uq_property_intermediary_active', postgresql_where=sa.text('is_active = true')),
    )
    
    # Indexes for property_assignments
    op.create_index('idx_pa_property', 'property_assignments', ['property_id'])
    op.create_index('idx_pa_intermediary', 'property_assignments', ['intermediary_id'])
    op.create_index('idx_pa_active', 'property_assignments', ['is_active'], postgresql_where=sa.text('is_active = true'))
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), comment='Tenant identifier'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, comment="Associated user account (must be role='tenant')"),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Rented property'),
        sa.Column('intermediary_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Managing intermediary'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False, comment='User who created tenant record'),
        sa.Column('move_in_date', sa.Date(), nullable=False, comment='Tenant move-in date'),
        sa.Column('move_out_date', sa.Date(), nullable=True, comment='Tenant move-out date'),
        sa.Column('monthly_rent', sa.Numeric(12, 2), nullable=False, comment='Monthly rent amount'),
        sa.Column('security_deposit', sa.Numeric(12, 2), nullable=True, comment='Security deposit amount'),
        sa.Column('electricity_rate', sa.Numeric(8, 4), nullable=True, comment='Per-unit electricity rate (for bill splitting)'),
        sa.Column('status', postgresql.ENUM('active', 'inactive', 'pending_move_out', name='tenant_status'), nullable=False, server_default=sa.text("'active'"), comment='Tenant status'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Last update timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['intermediary_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.CheckConstraint('monthly_rent > 0', name='check_monthly_rent_positive'),
        sa.CheckConstraint('move_out_date IS NULL OR move_out_date > move_in_date', name='check_move_out_after_move_in'),
    )
    
    # Indexes for tenants
    op.create_index('idx_tenants_user', 'tenants', ['user_id'])
    op.create_index('idx_tenants_property', 'tenants', ['property_id'])
    op.create_index('idx_tenants_intermediary', 'tenants', ['intermediary_id'])
    op.create_index('idx_tenants_status', 'tenants', ['status'])
    
    # Create payments table (stub for relationships)
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), comment='Payment identifier'),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Paying tenant'),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Related property'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False, comment='User who recorded payment'),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False, comment='Payment amount'),
        sa.Column('currency', sa.String(3), nullable=False, comment='ISO 4217 currency code'),
        sa.Column('payment_method', postgresql.ENUM('cash', 'bank_transfer', 'online', 'upi', 'card', 'other', name='payment_method'), nullable=False, comment='Payment method'),
        sa.Column('payment_type', postgresql.ENUM('rent', 'security_deposit', 'bill_share', 'penalty', 'other', name='payment_type'), nullable=False, comment='Type of payment'),
        sa.Column('payment_date', sa.Date(), nullable=False, comment='Date payment received'),
        sa.Column('reference_number', sa.String(100), nullable=True, comment='Transaction reference'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Additional notes'),
        sa.Column('receipt_url', sa.String(500), nullable=True, comment='S3 URL to receipt PDF'),
        sa.Column('device_id', sa.String(100), nullable=True, comment='Device that created record (for sync)'),
        sa.Column('is_voided', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='Payment voided flag'),
        sa.Column('voided_at', sa.DateTime(), nullable=True, comment='Void timestamp'),
        sa.Column('voided_by', postgresql.UUID(as_uuid=True), nullable=True, comment='User who voided payment'),
        sa.Column('void_reason', sa.Text(), nullable=True, comment='Reason for voiding'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Record creation timestamp'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['voided_by'], ['users.id'], ondelete='SET NULL'),
        sa.CheckConstraint('amount > 0', name='check_amount_positive'),
    )
    
    # Indexes for payments
    op.create_index('idx_payments_tenant', 'payments', ['tenant_id'])
    op.create_index('idx_payments_property', 'payments', ['property_id'])
    op.create_index('idx_payments_date', 'payments', [sa.text('payment_date DESC')])
    
    # Create bills table (minimal for bill_allocations FK)
    op.create_table(
        'bills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), comment='Bill identifier'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Record creation timestamp'),
    )
    
    # Create bill_allocations table (stub for relationships)
    op.create_table(
        'bill_allocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()'), comment='Allocation identifier'),
        sa.Column('bill_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Related bill'),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Allocated tenant'),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False, comment='Allocated amount'),
        sa.Column('is_paid', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='Payment status'),
        sa.Column('paid_at', sa.DateTime(), nullable=True, comment='Payment timestamp'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='Last update timestamp'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    
    # Indexes for bill_allocations
    op.create_index('idx_bill_allocations_bill', 'bill_allocations', ['bill_id'])
    op.create_index('idx_bill_allocations_tenant', 'bill_allocations', ['tenant_id'])


def downgrade() -> None:
    """Drop all tables and enums."""
    
    # Drop tables in reverse order
    op.drop_index('idx_bill_allocations_tenant', table_name='bill_allocations')
    op.drop_index('idx_bill_allocations_bill', table_name='bill_allocations')
    op.drop_table('bill_allocations')
    op.drop_table('bills')
    
    op.drop_index('idx_payments_date', table_name='payments')
    op.drop_index('idx_payments_property', table_name='payments')
    op.drop_index('idx_payments_tenant', table_name='payments')
    op.drop_table('payments')
    
    op.drop_index('idx_tenants_status', table_name='tenants')
    op.drop_index('idx_tenants_intermediary', table_name='tenants')
    op.drop_index('idx_tenants_property', table_name='tenants')
    op.drop_index('idx_tenants_user', table_name='tenants')
    op.drop_table('tenants')
    
    op.drop_index('idx_pa_active', table_name='property_assignments')
    op.drop_index('idx_pa_intermediary', table_name='property_assignments')
    op.drop_index('idx_pa_property', table_name='property_assignments')
    op.drop_table('property_assignments')
    
    op.drop_index('idx_properties_city', table_name='properties')
    op.drop_index('idx_properties_owner', table_name='properties')
    op.drop_table('properties')
    
    op.drop_index('idx_users_active', table_name='users')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS payment_type')
    op.execute('DROP TYPE IF EXISTS payment_method')
    op.execute('DROP TYPE IF EXISTS tenant_status')
    op.execute('DROP TYPE IF EXISTS user_role')
