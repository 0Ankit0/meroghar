"""add_payment_tables

Revision ID: 012cc4845c3b
Revises: 181485a25604
Create Date: 2026-02-25 06:04:39.091859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '012cc4845c3b'
down_revision: Union[str, Sequence[str], None] = '181485a25604'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

paymentprovider = sa.Enum(
    "khalti",
    "esewa",
    "stripe",
    "paypal",
    name="paymentprovider",
)
paymentstatus = sa.Enum(
    "pending",
    "initiated",
    "completed",
    "failed",
    "refunded",
    "cancelled",
    name="paymentstatus",
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", paymentprovider, nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sqlmodel.AutoString(length=3), nullable=False),
        sa.Column("status", paymentstatus, nullable=False),
        sa.Column("purchase_order_id", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("purchase_order_name", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("provider_transaction_id", sqlmodel.AutoString(length=255), nullable=True),
        sa.Column("provider_pidx", sqlmodel.AutoString(length=255), nullable=True),
        sa.Column("return_url", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("website_url", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("extra_data", sa.Text(), nullable=True),
        sa.Column("failure_reason", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("payment_transactions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_payment_transactions_provider_pidx"), ["provider_pidx"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_payment_transactions_provider_transaction_id"),
            ["provider_transaction_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_payment_transactions_purchase_order_id"),
            ["purchase_order_id"],
            unique=False,
        )

    op.create_table(
        "payment_webhooks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", paymentprovider, nullable=False),
        sa.Column("event_type", sqlmodel.AutoString(length=100), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("ip_address", sqlmodel.AutoString(length=45), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["payment_transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("payment_webhooks")

    with op.batch_alter_table("payment_transactions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_payment_transactions_purchase_order_id"))
        batch_op.drop_index(batch_op.f("ix_payment_transactions_provider_transaction_id"))
        batch_op.drop_index(batch_op.f("ix_payment_transactions_provider_pidx"))

    op.drop_table("payment_transactions")
