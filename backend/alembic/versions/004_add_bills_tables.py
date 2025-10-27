"""Add bills, bill_allocations, and recurring_bills tables

Implements T078 from tasks.md.

Revision ID: 004_add_bills_tables
Revises: 003_add_payments_tables
Create Date: 2025-10-27 10:32:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_add_bills_tables'
down_revision: Union[str, None] = '003_add_payments_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create bills, bill_allocations, and recurring_bills tables with enums."""
    
    # Create enum types
    op.execute("""
        CREATE TYPE bill_type AS ENUM (
            'electricity', 'water', 'gas', 'internet', 'maintenance', 'garbage', 'other'
        )
    """)
    
    op.execute("""
        CREATE TYPE bill_status AS ENUM (
            'pending', 'partially_paid', 'paid', 'overdue'
        )
    """)
    
    op.execute("""
        CREATE TYPE allocation_method AS ENUM (
            'equal', 'percentage', 'fixed_amount', 'custom'
        )
    """)
    
    op.execute("""
        CREATE TYPE recurring_frequency AS ENUM (
            'monthly', 'quarterly', 'yearly'
        )
    """)
    
    # Create bills table
    op.create_table(
        'bills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('properties.id'), nullable=False, index=True),
        sa.Column('bill_type', sa.Enum('electricity', 'water', 'gas', 'internet', 'maintenance', 'garbage', 'other', name='bill_type'), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False, index=True),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', sa.Enum('pending', 'partially_paid', 'paid', 'overdue', name='bill_status'), nullable=False, index=True),
        sa.Column('allocation_method', sa.Enum('equal', 'percentage', 'fixed_amount', 'custom', name='allocation_method'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bill_number', sa.String(100), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True, index=True),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create bill_allocations table
    op.create_table(
        'bill_allocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bills.id'), nullable=False, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('allocated_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('is_paid', sa.Boolean(), nullable=False, default=False),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.id'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create recurring_bills table
    op.create_table(
        'recurring_bills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('properties.id'), nullable=False, index=True),
        sa.Column('bill_type', sa.Enum('electricity', 'water', 'gas', 'internet', 'maintenance', 'garbage', 'other', name='bill_type'), nullable=False),
        sa.Column('frequency', sa.Enum('monthly', 'quarterly', 'yearly', name='recurring_frequency'), nullable=False),
        sa.Column('allocation_method', sa.Enum('equal', 'percentage', 'fixed_amount', 'custom', name='allocation_method'), nullable=False),
        sa.Column('estimated_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('day_of_month', sa.Integer(), nullable=False, default=1),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_generated', sa.Date(), nullable=True),
        sa.Column('next_generation', sa.Date(), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop bills tables and enums."""
    
    op.drop_table('recurring_bills')
    op.drop_table('bill_allocations')
    op.drop_table('bills')
    
    op.execute("DROP TYPE IF EXISTS recurring_frequency")
    op.execute("DROP TYPE IF EXISTS allocation_method")
    op.execute("DROP TYPE IF EXISTS bill_status")
    op.execute("DROP TYPE IF EXISTS bill_type")