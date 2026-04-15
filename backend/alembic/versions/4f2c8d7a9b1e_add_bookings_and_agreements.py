"""add_bookings_and_agreements

Revision ID: 4f2c8d7a9b1e
Revises: c3e4f5a6b7c8
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "4f2c8d7a9b1e"
down_revision: Union[str, Sequence[str], None] = "c3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


bookingstatus = sa.Enum(
    "PENDING",
    "CONFIRMED",
    "DECLINED",
    "CANCELLED",
    "ACTIVE",
    "PENDING_CLOSURE",
    "CLOSED",
    name="bookingstatus",
)
securitydepositstatus = sa.Enum(
    "HELD",
    "FULLY_REFUNDED",
    "PARTIALLY_REFUNDED",
    "FULLY_DEDUCTED",
    "DISPUTED",
    name="securitydepositstatus",
)
agreementstatus = sa.Enum(
    "DRAFT",
    "PENDING_CUSTOMER_SIGNATURE",
    "PENDING_OWNER_SIGNATURE",
    "SIGNED",
    "AMENDED",
    "TERMINATED",
    name="agreementstatus",
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_number", sqlmodel.AutoString(length=32), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("tenant_user_id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("status", bookingstatus, nullable=False),
        sa.Column("rental_start_at", sa.DateTime(), nullable=False),
        sa.Column("rental_end_at", sa.DateTime(), nullable=False),
        sa.Column("actual_return_at", sa.DateTime(), nullable=True),
        sa.Column("special_requests", sqlmodel.AutoString(length=2000), nullable=False),
        sa.Column("payment_method_id", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("currency", sqlmodel.AutoString(length=3), nullable=False),
        sa.Column("base_fee", sa.Float(), nullable=False),
        sa.Column("peak_surcharge", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), nullable=False),
        sa.Column("total_fee", sa.Float(), nullable=False),
        sa.Column("deposit_amount", sa.Float(), nullable=False),
        sa.Column("decline_reason", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("cancellation_reason", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("declined_at", sa.DateTime(), nullable=True),
        sa.Column("refund_amount", sa.Float(), nullable=False),
        sa.Column("idempotency_key", sqlmodel.AutoString(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.ForeignKeyConstraint(["tenant_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_number", name="uq_bookings_booking_number"),
        sa.UniqueConstraint("tenant_user_id", "idempotency_key", name="uq_bookings_tenant_idempotency_key"),
    )
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_bookings_booking_number"), ["booking_number"], unique=True)
        batch_op.create_index(batch_op.f("ix_bookings_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookings_idempotency_key"), ["idempotency_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookings_owner_user_id"), ["owner_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookings_property_id"), ["property_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookings_rental_end_at"), ["rental_end_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookings_rental_start_at"), ["rental_start_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookings_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_bookings_tenant_user_id"), ["tenant_user_id"], unique=False)

    op.create_table(
        "booking_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sqlmodel.AutoString(length=100), nullable=False),
        sa.Column("message", sqlmodel.AutoString(length=2000), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("booking_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_booking_events_actor_user_id"), ["actor_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_booking_events_booking_id"), ["booking_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_booking_events_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_booking_events_event_type"), ["event_type"], unique=False)

    op.create_table(
        "cancellation_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("free_cancellation_hours", sa.Integer(), nullable=False),
        sa.Column("partial_refund_hours", sa.Integer(), nullable=False),
        sa.Column("partial_refund_percent", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("property_id"),
    )
    with op.batch_alter_table("cancellation_policies", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_cancellation_policies_property_id"), ["property_id"], unique=True)

    op.create_table(
        "security_deposits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", securitydepositstatus, nullable=False),
        sa.Column("gateway_ref", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("deduction_total", sa.Float(), nullable=False),
        sa.Column("refund_amount", sa.Float(), nullable=False),
        sa.Column("collected_at", sa.DateTime(), nullable=True),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id"),
    )
    with op.batch_alter_table("security_deposits", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_security_deposits_booking_id"), ["booking_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_security_deposits_status"), ["status"], unique=False)

    op.create_table(
        "agreement_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_by_admin_id", sa.Integer(), nullable=False),
        sa.Column("property_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=150), nullable=False),
        sa.Column("template_content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["property_type_id"], ["property_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("agreement_templates", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_agreement_templates_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_agreement_templates_created_by_admin_id"), ["created_by_admin_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_agreement_templates_is_active"), ["is_active"], unique=False)
        batch_op.create_index(batch_op.f("ix_agreement_templates_property_type_id"), ["property_type_id"], unique=False)

    op.create_table(
        "rental_agreements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("status", agreementstatus, nullable=False),
        sa.Column("rendered_content", sa.Text(), nullable=False),
        sa.Column("custom_clauses_json", sa.JSON(), nullable=False),
        sa.Column("rendered_document_url", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("rendered_document_sha256", sqlmodel.AutoString(length=64), nullable=True),
        sa.Column("esign_request_id", sqlmodel.AutoString(length=120), nullable=True),
        sa.Column("signed_document_url", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("signed_document_sha256", sqlmodel.AutoString(length=64), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("customer_signed_at", sa.DateTime(), nullable=True),
        sa.Column("customer_signature_ip", sqlmodel.AutoString(length=45), nullable=True),
        sa.Column("owner_signed_at", sa.DateTime(), nullable=True),
        sa.Column("owner_signature_ip", sqlmodel.AutoString(length=45), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["agreement_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("esign_request_id"),
    )
    with op.batch_alter_table("rental_agreements", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_rental_agreements_booking_id"), ["booking_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_rental_agreements_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_rental_agreements_esign_request_id"), ["esign_request_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_rental_agreements_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_rental_agreements_template_id"), ["template_id"], unique=False)

    op.create_table(
        "agreement_amendments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agreement_id", sa.Integer(), nullable=False),
        sa.Column("amendment_number", sa.Integer(), nullable=False),
        sa.Column("reason", sqlmodel.AutoString(length=1000), nullable=False),
        sa.Column("signed_document_url", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("status", sqlmodel.AutoString(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agreement_id"], ["rental_agreements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("agreement_amendments", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_agreement_amendments_agreement_id"), ["agreement_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_agreement_amendments_created_at"), ["created_at"], unique=False)

    with op.batch_alter_table("availability_blocks", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_availability_blocks_booking_id"), ["booking_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_availability_blocks_booking_id_bookings",
            "bookings",
            ["booking_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("availability_blocks", schema=None) as batch_op:
        batch_op.drop_constraint("fk_availability_blocks_booking_id_bookings", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_availability_blocks_booking_id"))

    with op.batch_alter_table("agreement_amendments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_agreement_amendments_created_at"))
        batch_op.drop_index(batch_op.f("ix_agreement_amendments_agreement_id"))
    op.drop_table("agreement_amendments")

    with op.batch_alter_table("rental_agreements", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_rental_agreements_template_id"))
        batch_op.drop_index(batch_op.f("ix_rental_agreements_status"))
        batch_op.drop_index(batch_op.f("ix_rental_agreements_esign_request_id"))
        batch_op.drop_index(batch_op.f("ix_rental_agreements_created_at"))
        batch_op.drop_index(batch_op.f("ix_rental_agreements_booking_id"))
    op.drop_table("rental_agreements")

    with op.batch_alter_table("agreement_templates", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_agreement_templates_property_type_id"))
        batch_op.drop_index(batch_op.f("ix_agreement_templates_is_active"))
        batch_op.drop_index(batch_op.f("ix_agreement_templates_created_by_admin_id"))
        batch_op.drop_index(batch_op.f("ix_agreement_templates_created_at"))
    op.drop_table("agreement_templates")

    with op.batch_alter_table("security_deposits", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_security_deposits_status"))
        batch_op.drop_index(batch_op.f("ix_security_deposits_booking_id"))
    op.drop_table("security_deposits")

    with op.batch_alter_table("cancellation_policies", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cancellation_policies_property_id"))
    op.drop_table("cancellation_policies")

    with op.batch_alter_table("booking_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_booking_events_event_type"))
        batch_op.drop_index(batch_op.f("ix_booking_events_created_at"))
        batch_op.drop_index(batch_op.f("ix_booking_events_booking_id"))
        batch_op.drop_index(batch_op.f("ix_booking_events_actor_user_id"))
    op.drop_table("booking_events")

    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bookings_tenant_user_id"))
        batch_op.drop_index(batch_op.f("ix_bookings_status"))
        batch_op.drop_index(batch_op.f("ix_bookings_rental_start_at"))
        batch_op.drop_index(batch_op.f("ix_bookings_rental_end_at"))
        batch_op.drop_index(batch_op.f("ix_bookings_property_id"))
        batch_op.drop_index(batch_op.f("ix_bookings_owner_user_id"))
        batch_op.drop_index(batch_op.f("ix_bookings_idempotency_key"))
        batch_op.drop_index(batch_op.f("ix_bookings_created_at"))
        batch_op.drop_index(batch_op.f("ix_bookings_booking_number"))
    op.drop_table("bookings")
