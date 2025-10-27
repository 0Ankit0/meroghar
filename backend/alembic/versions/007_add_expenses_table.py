"""Add expenses table for maintenance tracking

Revision ID: 007
Revises: 006
Create Date: 2025-01-27 13:00:00.000000

Implements T126 from tasks.md - Add Expense table for tracking maintenance
and operational expenses requiring owner reimbursement.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create expenses table and related enums."""
    
    # Create expense_category enum
    op.execute("""
        CREATE TYPE expense_category AS ENUM (
            'maintenance',
            'repair',
            'cleaning',
            'landscaping',
            'security',
            'utilities',
            'insurance',
            'taxes',
            'legal',
            'administrative',
            'other'
        )
    """)
    
    # Create expense_status enum
    op.execute("""
        CREATE TYPE expense_status AS ENUM (
            'pending',
            'approved',
            'rejected',
            'reimbursed'
        )
    """)
    
    # Create expenses table
    op.create_table(
        'expenses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('property_id', UUID(as_uuid=True), nullable=False),
        sa.Column('recorded_by', UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='NPR'),
        sa.Column('category', sa.Enum(
            'maintenance', 'repair', 'cleaning', 'landscaping', 'security',
            'utilities', 'insurance', 'taxes', 'legal', 'administrative', 'other',
            name='expense_category',
            create_type=False
        ), nullable=False),
        sa.Column('status', sa.Enum(
            'pending', 'approved', 'rejected', 'reimbursed',
            name='expense_status',
            create_type=False
        ), nullable=False, server_default='pending'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('vendor_name', sa.String(length=255), nullable=True),
        sa.Column('invoice_number', sa.String(length=100), nullable=True),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('paid_by', sa.String(length=100), nullable=False, server_default='intermediary'),
        sa.Column('is_reimbursable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_reimbursed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reimbursed_date', sa.Date(), nullable=True),
        sa.Column('expense_date', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('approved_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Create indexes
    op.create_index('ix_expenses_property_id', 'expenses', ['property_id'])
    op.create_index('ix_expenses_recorded_by', 'expenses', ['recorded_by'])
    op.create_index('ix_expenses_approved_by', 'expenses', ['approved_by'])
    op.create_index('ix_expenses_status', 'expenses', ['status'])
    op.create_index('ix_expenses_expense_date', 'expenses', ['expense_date'])
    op.create_index('ix_expenses_category', 'expenses', ['category'])


def downgrade() -> None:
    """Drop expenses table and related enums."""
    
    # Drop indexes
    op.drop_index('ix_expenses_category', table_name='expenses')
    op.drop_index('ix_expenses_expense_date', table_name='expenses')
    op.drop_index('ix_expenses_status', table_name='expenses')
    op.drop_index('ix_expenses_approved_by', table_name='expenses')
    op.drop_index('ix_expenses_recorded_by', table_name='expenses')
    op.drop_index('ix_expenses_property_id', table_name='expenses')
    
    # Drop table
    op.drop_table('expenses')
    
    # Drop enums
    op.execute('DROP TYPE expense_status')
    op.execute('DROP TYPE expense_category')
