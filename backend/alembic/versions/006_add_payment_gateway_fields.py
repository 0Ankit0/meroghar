"""Add payment gateway tracking fields

Revision ID: 006
Revises: 005
Create Date: 2025-01-27 12:00:00.000000

Implements T124 from tasks.md - Add payment gateway fee tracking.

Adds:
- gateway_transaction_id: Track transaction ID from payment gateways (Khalti, eSewa, IME Pay)
- gateway_fee: Track fees charged by payment gateways
- metadata: Store gateway-specific information (pidx, callback data, etc.) as JSONB

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add payment gateway tracking fields to payments table."""
    
    # Add gateway_transaction_id column
    op.add_column(
        'payments',
        sa.Column(
            'gateway_transaction_id',
            sa.String(length=255),
            nullable=True,
        )
    )
    
    # Add index on gateway_transaction_id for quick lookups
    op.create_index(
        'ix_payments_gateway_transaction_id',
        'payments',
        ['gateway_transaction_id'],
        unique=False
    )
    
    # Add gateway_fee column
    op.add_column(
        'payments',
        sa.Column(
            'gateway_fee',
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            server_default='0.00'
        )
    )
    
    # Add metadata column for storing gateway-specific data
    op.add_column(
        'payments',
        sa.Column(
            'metadata',
            JSONB,
            nullable=True
        )
    )


def downgrade() -> None:
    """Remove payment gateway tracking fields."""
    
    # Remove metadata column
    op.drop_column('payments', 'metadata')
    
    # Remove gateway_fee column
    op.drop_column('payments', 'gateway_fee')
    
    # Remove index and column for gateway_transaction_id
    op.drop_index('ix_payments_gateway_transaction_id', table_name='payments')
    op.drop_column('payments', 'gateway_transaction_id')
