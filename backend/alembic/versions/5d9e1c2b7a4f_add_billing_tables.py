"""add_billing_tables

Revision ID: 5d9e1c2b7a4f
Revises: 4f2c8d7a9b1e
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "5d9e1c2b7a4f"
down_revision: Union[str, Sequence[str], None] = "4f2c8d7a9b1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

invoicetype = sa.Enum(
    "rent",
    "additional_charge",
    "utility_bill_share",
    name="invoicetype",
)
invoicestatus = sa.Enum(
    "draft",
    "sent",
    "partially_paid",
    "paid",
    "overdue",
    "waived",
    name="invoicestatus",
)
invoiceremindertype = sa.Enum(
    "t_minus_7",
    "t_minus_3",
    "t_minus_1",
    "overdue",
    name="invoiceremindertype",
)
invoicereminderstatus = sa.Enum(
    "scheduled",
    "sent",
    "skipped",
    name="invoicereminderstatus",
)
paymentreferencetype = sa.Enum(
    "invoice",
    "security_deposit",
    name="paymentreferencetype",
)
paymentprovider = sa.Enum(
    "khalti",
    "esewa",
    "stripe",
    "paypal",
    name="paymentprovider",
    create_type=False,
)
paymentstatus = sa.Enum(
    "pending",
    "initiated",
    "completed",
    "failed",
    "refunded",
    "cancelled",
    name="paymentstatus",
    create_type=False,
)
refundstatus = sa.Enum(
    "initiated",
    "completed",
    "failed",
    name="refundstatus",
)
additionalchargestatus = sa.Enum(
    "raised",
    "accepted",
    "disputed",
    "partially_accepted",
    "paid",
    "waived",
    name="additionalchargestatus",
)
utilitybilltype = sa.Enum(
    "electricity",
    "water",
    "internet",
    "gas",
    "other",
    name="utilitybilltype",
)
utilitybillstatus = sa.Enum(
    "draft",
    "published",
    "partially_paid",
    "settled",
    name="utilitybillstatus",
)
utilitybillsplitmethod = sa.Enum(
    "single",
    "equal",
    "percentage",
    "fixed",
    name="utilitybillsplitmethod",
)
utilitybillsplitstatus = sa.Enum(
    "pending",
    "partially_paid",
    "paid",
    "disputed",
    "waived",
    name="utilitybillsplitstatus",
)
utilitybilldisputestatus = sa.Enum(
    "open",
    "resolved",
    "rejected",
    "waived",
    name="utilitybilldisputestatus",
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sqlmodel.AutoString(length=40), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        sa.Column("tenant_user_id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("invoice_type", invoicetype, nullable=False),
        sa.Column("currency", sqlmodel.AutoString(length=3), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("paid_amount", sa.Float(), nullable=False),
        sa.Column("status", invoicestatus, nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["tenant_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_number", name="uq_invoices_invoice_number"),
    )
    with op.batch_alter_table("invoices", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_invoices_booking_id"), ["booking_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_invoices_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_invoices_due_date"), ["due_date"], unique=False)
        batch_op.create_index(batch_op.f("ix_invoices_invoice_number"), ["invoice_number"], unique=True)
        batch_op.create_index(batch_op.f("ix_invoices_invoice_type"), ["invoice_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_invoices_owner_user_id"), ["owner_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_invoices_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_invoices_tenant_user_id"), ["tenant_user_id"], unique=False)

    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("line_item_type", sqlmodel.AutoString(length=80), nullable=False),
        sa.Column("description", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("tax_rate", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("invoice_line_items", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_invoice_line_items_invoice_id"), ["invoice_id"], unique=False)

    op.create_table(
        "invoice_reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("reminder_type", invoiceremindertype, nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("status", invoicereminderstatus, nullable=False),
        sa.Column("channel_status_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("invoice_reminders", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_invoice_reminders_invoice_id"), ["invoice_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_invoice_reminders_reminder_type"), ["reminder_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_invoice_reminders_scheduled_for"), ["scheduled_for"], unique=False)
        batch_op.create_index(batch_op.f("ix_invoice_reminders_status"), ["status"], unique=False)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference_type", paymentreferencetype, nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.Column("payer_user_id", sa.Integer(), nullable=False),
        sa.Column("payment_method", paymentprovider, nullable=False),
        sa.Column("status", paymentstatus, nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sqlmodel.AutoString(length=3), nullable=False),
        sa.Column("gateway_ref", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("gateway_response_json", sa.JSON(), nullable=True),
        sa.Column("is_offline", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["payer_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("payments", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_payments_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_payments_gateway_ref"), ["gateway_ref"], unique=False)
        batch_op.create_index(batch_op.f("ix_payments_payer_user_id"), ["payer_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_payments_payment_method"), ["payment_method"], unique=False)
        batch_op.create_index(batch_op.f("ix_payments_reference_id"), ["reference_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_payments_reference_type"), ["reference_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_payments_status"), ["status"], unique=False)

    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("gateway_ref", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", refundstatus, nullable=False),
        sa.Column("reason", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("initiated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("refunds", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_refunds_initiated_at"), ["initiated_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_refunds_payment_id"), ["payment_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_refunds_status"), ["status"], unique=False)

    op.create_table(
        "additional_charges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("charge_type", sqlmodel.AutoString(length=80), nullable=False),
        sa.Column("description", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("resolved_amount", sa.Float(), nullable=True),
        sa.Column("evidence_url", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("status", additionalchargestatus, nullable=False),
        sa.Column("dispute_reason", sqlmodel.AutoString(length=1000), nullable=False),
        sa.Column("resolution_notes", sqlmodel.AutoString(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_id", name="uq_additional_charges_invoice_id"),
    )
    with op.batch_alter_table("additional_charges", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_additional_charges_booking_id"), ["booking_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_additional_charges_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_additional_charges_invoice_id"), ["invoice_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_additional_charges_status"), ["status"], unique=False)

    op.create_table(
        "utility_bills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("bill_type", utilitybilltype, nullable=False),
        sa.Column("billing_period_label", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("owner_subsidy_amount", sa.Float(), nullable=False),
        sa.Column("status", utilitybillstatus, nullable=False),
        sa.Column("notes", sqlmodel.AutoString(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("utility_bills", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_utility_bills_bill_type"), ["bill_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bills_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bills_created_by_user_id"), ["created_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bills_property_id"), ["property_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bills_status"), ["status"], unique=False)

    op.create_table(
        "utility_bill_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utility_bill_id", sa.Integer(), nullable=False),
        sa.Column("file_url", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("file_type", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("checksum", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["utility_bill_id"], ["utility_bills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("utility_bill_attachments", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_utility_bill_attachments_uploaded_at"), ["uploaded_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bill_attachments_utility_bill_id"), ["utility_bill_id"], unique=False)

    op.create_table(
        "utility_bill_splits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utility_bill_id", sa.Integer(), nullable=False),
        sa.Column("tenant_user_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("split_method", utilitybillsplitmethod, nullable=False),
        sa.Column("split_percent", sa.Float(), nullable=True),
        sa.Column("assigned_amount", sa.Float(), nullable=False),
        sa.Column("paid_amount", sa.Float(), nullable=False),
        sa.Column("status", utilitybillsplitstatus, nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["tenant_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["utility_bill_id"], ["utility_bills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_id", name="uq_utility_bill_splits_invoice_id"),
    )
    with op.batch_alter_table("utility_bill_splits", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_utility_bill_splits_invoice_id"), ["invoice_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_utility_bill_splits_split_method"), ["split_method"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bill_splits_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bill_splits_tenant_user_id"), ["tenant_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bill_splits_utility_bill_id"), ["utility_bill_id"], unique=False)

    op.create_table(
        "utility_bill_disputes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("utility_bill_split_id", sa.Integer(), nullable=False),
        sa.Column("opened_by_user_id", sa.Integer(), nullable=False),
        sa.Column("status", utilitybilldisputestatus, nullable=False),
        sa.Column("reason", sqlmodel.AutoString(length=1000), nullable=False),
        sa.Column("resolution_notes", sqlmodel.AutoString(length=1000), nullable=False),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["opened_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["utility_bill_split_id"], ["utility_bill_splits.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("utility_bill_disputes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_utility_bill_disputes_opened_at"), ["opened_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bill_disputes_opened_by_user_id"), ["opened_by_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bill_disputes_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_utility_bill_disputes_utility_bill_split_id"), ["utility_bill_split_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("utility_bill_disputes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_utility_bill_disputes_utility_bill_split_id"))
        batch_op.drop_index(batch_op.f("ix_utility_bill_disputes_status"))
        batch_op.drop_index(batch_op.f("ix_utility_bill_disputes_opened_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_utility_bill_disputes_opened_at"))
    op.drop_table("utility_bill_disputes")

    with op.batch_alter_table("utility_bill_splits", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_utility_bill_splits_utility_bill_id"))
        batch_op.drop_index(batch_op.f("ix_utility_bill_splits_tenant_user_id"))
        batch_op.drop_index(batch_op.f("ix_utility_bill_splits_status"))
        batch_op.drop_index(batch_op.f("ix_utility_bill_splits_split_method"))
        batch_op.drop_index(batch_op.f("ix_utility_bill_splits_invoice_id"))
    op.drop_table("utility_bill_splits")

    with op.batch_alter_table("utility_bill_attachments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_utility_bill_attachments_utility_bill_id"))
        batch_op.drop_index(batch_op.f("ix_utility_bill_attachments_uploaded_at"))
    op.drop_table("utility_bill_attachments")

    with op.batch_alter_table("utility_bills", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_utility_bills_status"))
        batch_op.drop_index(batch_op.f("ix_utility_bills_property_id"))
        batch_op.drop_index(batch_op.f("ix_utility_bills_created_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_utility_bills_created_at"))
        batch_op.drop_index(batch_op.f("ix_utility_bills_bill_type"))
    op.drop_table("utility_bills")

    with op.batch_alter_table("additional_charges", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_additional_charges_status"))
        batch_op.drop_index(batch_op.f("ix_additional_charges_invoice_id"))
        batch_op.drop_index(batch_op.f("ix_additional_charges_created_at"))
        batch_op.drop_index(batch_op.f("ix_additional_charges_booking_id"))
    op.drop_table("additional_charges")

    with op.batch_alter_table("refunds", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_refunds_status"))
        batch_op.drop_index(batch_op.f("ix_refunds_payment_id"))
        batch_op.drop_index(batch_op.f("ix_refunds_initiated_at"))
    op.drop_table("refunds")

    with op.batch_alter_table("payments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_payments_status"))
        batch_op.drop_index(batch_op.f("ix_payments_reference_type"))
        batch_op.drop_index(batch_op.f("ix_payments_reference_id"))
        batch_op.drop_index(batch_op.f("ix_payments_payment_method"))
        batch_op.drop_index(batch_op.f("ix_payments_payer_user_id"))
        batch_op.drop_index(batch_op.f("ix_payments_gateway_ref"))
        batch_op.drop_index(batch_op.f("ix_payments_created_at"))
    op.drop_table("payments")

    with op.batch_alter_table("invoice_reminders", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_invoice_reminders_status"))
        batch_op.drop_index(batch_op.f("ix_invoice_reminders_scheduled_for"))
        batch_op.drop_index(batch_op.f("ix_invoice_reminders_reminder_type"))
        batch_op.drop_index(batch_op.f("ix_invoice_reminders_invoice_id"))
    op.drop_table("invoice_reminders")

    with op.batch_alter_table("invoice_line_items", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_invoice_line_items_invoice_id"))
    op.drop_table("invoice_line_items")

    with op.batch_alter_table("invoices", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_invoices_tenant_user_id"))
        batch_op.drop_index(batch_op.f("ix_invoices_status"))
        batch_op.drop_index(batch_op.f("ix_invoices_owner_user_id"))
        batch_op.drop_index(batch_op.f("ix_invoices_invoice_type"))
        batch_op.drop_index(batch_op.f("ix_invoices_invoice_number"))
        batch_op.drop_index(batch_op.f("ix_invoices_due_date"))
        batch_op.drop_index(batch_op.f("ix_invoices_created_at"))
        batch_op.drop_index(batch_op.f("ix_invoices_booking_id"))
    op.drop_table("invoices")
