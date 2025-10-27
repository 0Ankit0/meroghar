"""Add payments and transactions tables

Implements T058 from tasks.md.

Revision ID: 003_add_payments_tables
Revises: 002_add_rls_policies
Create Date: 2025-10-27 08:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_payments_tables'
down_revision: Union[str, None] = '002_add_rls_policies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create payments and transactions tables with enums."""
    
    # Create enum types for payment_method, payment_type, payment_status
    op.execute("""
        CREATE TYPE payment_method AS ENUM (
            'cash', 'bank_transfer', 'upi', 'cheque', 'card', 'online'
        )
    """)
    
    op.execute("""
        CREATE TYPE payment_type AS ENUM (
            'rent', 'security_deposit', 'utility', 'maintenance', 'other'
        )
    """)
    
    op.execute("""
        CREATE TYPE payment_status AS ENUM (
            'pending', 'completed', 'failed', 'refunded'
        )
    """)
    
    op.execute("""
        CREATE TYPE transaction_status AS ENUM (
            'initiated', 'processing', 'success', 'failed', 'cancelled'
        )
    """)
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('payment_method', sa.Enum('cash', 'bank_transfer', 'upi', 'cheque', 'card', 'online', name='payment_method'), nullable=False, server_default='cash'),
        sa.Column('payment_type', sa.Enum('rent', 'security_deposit', 'utility', 'maintenance', 'other', name='payment_type'), nullable=False, server_default='rent'),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'refunded', name='payment_status'), nullable=False, server_default='completed'),
        sa.Column('payment_period_start', sa.Date(), nullable=True),
        sa.Column('payment_period_end', sa.Date(), nullable=True),
        sa.Column('transaction_reference', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('payment_date', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount > 0', name='check_payment_amount_positive')
    )
    
    # Create indexes on payments table
    op.create_index('ix_payments_tenant_id', 'payments', ['tenant_id'])
    op.create_index('ix_payments_property_id', 'payments', ['property_id'])
    op.create_index('ix_payments_payment_date', 'payments', ['payment_date'], postgresql_ops={'payment_date': 'DESC'})
    op.create_index('ix_payments_transaction_reference', 'payments', ['transaction_reference'])
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gateway_name', sa.String(length=50), nullable=False),
        sa.Column('gateway_transaction_id', sa.String(length=255), nullable=False),
        sa.Column('gateway_order_id', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('status', sa.Enum('initiated', 'processing', 'success', 'failed', 'cancelled', name='transaction_status'), nullable=False, server_default='initiated'),
        sa.Column('gateway_response', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('initiated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gateway_transaction_id', name='uq_transactions_gateway_transaction_id')
    )
    
    # Create indexes on transactions table
    op.create_index('ix_transactions_gateway_transaction_id', 'transactions', ['gateway_transaction_id'], unique=True)
    op.create_index('ix_transactions_gateway_order_id', 'transactions', ['gateway_order_id'])
    op.create_index('ix_transactions_payment_id', 'transactions', ['payment_id'])


def downgrade() -> None:
    """Drop payments and transactions tables."""
    
    # Drop indexes
    op.drop_index('ix_transactions_payment_id', table_name='transactions')
    op.drop_index('ix_transactions_gateway_order_id', table_name='transactions')
    op.drop_index('ix_transactions_gateway_transaction_id', table_name='transactions')
    
    op.drop_index('ix_payments_transaction_reference', table_name='payments')
    op.drop_index('ix_payments_payment_date', table_name='payments')
    op.drop_index('ix_payments_property_id', table_name='payments')
    op.drop_index('ix_payments_tenant_id', table_name='payments')
    
    # Drop tables
    op.drop_table('transactions')
    op.drop_table('payments')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS transaction_status')
    op.execute('DROP TYPE IF EXISTS payment_status')
    op.execute('DROP TYPE IF EXISTS payment_type')
    op.execute('DROP TYPE IF EXISTS payment_method')
