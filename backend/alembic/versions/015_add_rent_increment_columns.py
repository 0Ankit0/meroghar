"""add rent increment columns to tenants

Revision ID: 015
Revises: 014
Create Date: 2025-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision: str = "015"
down_revision: Union[str, None] = "014"
branch_label: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rent increment policy and history columns to tenants table."""
    # Add rent_increment_policy column
    op.add_column(
        "tenants",
        sa.Column(
            "rent_increment_policy",
            JSON,
            nullable=True,
            comment="Rent increment policy: {type: 'percentage'|'fixed', value: number, interval_years: number, next_increment_date: ISO date}",
        ),
    )

    # Add rent_history column with default empty list
    op.add_column(
        "tenants",
        sa.Column(
            "rent_history",
            JSON,
            nullable=True,
            comment="Historical rent changes: [{effective_date: ISO, amount: Decimal, reason: str, applied_by: UUID}]",
        ),
    )


def downgrade() -> None:
    """Remove rent increment columns from tenants table."""
    op.drop_column("tenants", "rent_history")
    op.drop_column("tenants", "rent_increment_policy")
