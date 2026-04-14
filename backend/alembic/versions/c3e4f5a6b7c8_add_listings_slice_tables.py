"""add_listings_slice_tables

Revision ID: c3e4f5a6b7c8
Revises: b7c1d2e3f4a5
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "c3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "b7c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


propertyfeatureattributetype = sa.Enum(
    "TEXT",
    "NUMBER",
    "BOOLEAN",
    "SELECT",
    "MULTISELECT",
    name="propertyfeatureattributetype",
)
propertystatus = sa.Enum("DRAFT", "PUBLISHED", "ARCHIVED", name="propertystatus")
pricingratetype = sa.Enum("DAILY", "WEEKLY", "MONTHLY", name="pricingratetype")
availabilityblocktype = sa.Enum("MANUAL", "BOOKING", "MAINTENANCE", name="availabilityblocktype")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "property_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_category_id", sa.Integer(), nullable=True),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("slug", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("description", sqlmodel.AutoString(length=1000), nullable=False),
        sa.Column("icon_url", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["parent_category_id"], ["property_types.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    with op.batch_alter_table("property_types", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_property_types_display_order"), ["display_order"], unique=False)
        batch_op.create_index(batch_op.f("ix_property_types_is_active"), ["is_active"], unique=False)
        batch_op.create_index(batch_op.f("ix_property_types_name"), ["name"], unique=False)
        batch_op.create_index(batch_op.f("ix_property_types_slug"), ["slug"], unique=True)

    op.create_table(
        "property_type_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("slug", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("attribute_type", propertyfeatureattributetype, nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_filterable", sa.Boolean(), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["property_type_id"], ["property_types.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("property_type_id", "slug", name="uq_property_type_features_property_type_slug"),
    )
    with op.batch_alter_table("property_type_features", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_property_type_features_attribute_type"), ["attribute_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_property_type_features_display_order"), ["display_order"], unique=False)
        batch_op.create_index(batch_op.f("ix_property_type_features_property_type_id"), ["property_type_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_property_type_features_slug"), ["slug"], unique=False)

    op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("property_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=200), nullable=False),
        sa.Column("description", sqlmodel.AutoString(length=5000), nullable=False),
        sa.Column("status", propertystatus, nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("location_address", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lng", sa.Float(), nullable=True),
        sa.Column("deposit_amount", sa.Float(), nullable=False),
        sa.Column("min_rental_duration_hours", sa.Integer(), nullable=False),
        sa.Column("max_rental_duration_days", sa.Integer(), nullable=False),
        sa.Column("booking_lead_time_hours", sa.Integer(), nullable=False),
        sa.Column("instant_booking_enabled", sa.Boolean(), nullable=False),
        sa.Column("average_rating", sa.Float(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["property_type_id"], ["property_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_properties_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_properties_is_published"), ["is_published"], unique=False)
        batch_op.create_index(batch_op.f("ix_properties_location_address"), ["location_address"], unique=False)
        batch_op.create_index(batch_op.f("ix_properties_name"), ["name"], unique=False)
        batch_op.create_index(batch_op.f("ix_properties_owner_user_id"), ["owner_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_properties_property_type_id"), ["property_type_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_properties_status"), ["status"], unique=False)

    op.create_table(
        "property_feature_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("attribute_id", sa.Integer(), nullable=False),
        sa.Column("value", sqlmodel.AutoString(length=2000), nullable=False),
        sa.ForeignKeyConstraint(["attribute_id"], ["property_type_features.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("property_id", "attribute_id", name="uq_property_feature_values_property_attribute"),
    )
    with op.batch_alter_table("property_feature_values", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_property_feature_values_attribute_id"), ["attribute_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_property_feature_values_property_id"), ["property_id"], unique=False)

    op.create_table(
        "property_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("url", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("thumbnail_url", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_cover", sa.Boolean(), nullable=False),
        sa.Column("caption", sqlmodel.AutoString(length=255), nullable=False),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("property_photos", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_property_photos_is_cover"), ["is_cover"], unique=False)
        batch_op.create_index(batch_op.f("ix_property_photos_position"), ["position"], unique=False)
        batch_op.create_index(batch_op.f("ix_property_photos_property_id"), ["property_id"], unique=False)

    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("rate_type", pricingratetype, nullable=False),
        sa.Column("rate_amount", sa.Float(), nullable=False),
        sa.Column("currency", sqlmodel.AutoString(length=3), nullable=False),
        sa.Column("is_peak_rate", sa.Boolean(), nullable=False),
        sa.Column("peak_start_date", sa.Date(), nullable=True),
        sa.Column("peak_end_date", sa.Date(), nullable=True),
        sa.Column("peak_days_of_week_json", sa.JSON(), nullable=False),
        sa.Column("discount_percentage", sa.Float(), nullable=False),
        sa.Column("min_units_for_discount", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("pricing_rules", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_pricing_rules_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_pricing_rules_is_peak_rate"), ["is_peak_rate"], unique=False)
        batch_op.create_index(batch_op.f("ix_pricing_rules_property_id"), ["property_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_pricing_rules_rate_type"), ["rate_type"], unique=False)

    op.create_table(
        "availability_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("block_type", availabilityblocktype, nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        sa.Column("maintenance_request_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("availability_blocks", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_availability_blocks_block_type"), ["block_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_availability_blocks_end_at"), ["end_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_availability_blocks_property_id"), ["property_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_availability_blocks_start_at"), ["start_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("availability_blocks", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_availability_blocks_start_at"))
        batch_op.drop_index(batch_op.f("ix_availability_blocks_property_id"))
        batch_op.drop_index(batch_op.f("ix_availability_blocks_end_at"))
        batch_op.drop_index(batch_op.f("ix_availability_blocks_block_type"))
    op.drop_table("availability_blocks")

    with op.batch_alter_table("pricing_rules", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pricing_rules_rate_type"))
        batch_op.drop_index(batch_op.f("ix_pricing_rules_property_id"))
        batch_op.drop_index(batch_op.f("ix_pricing_rules_is_peak_rate"))
        batch_op.drop_index(batch_op.f("ix_pricing_rules_created_at"))
    op.drop_table("pricing_rules")

    with op.batch_alter_table("property_photos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_property_photos_property_id"))
        batch_op.drop_index(batch_op.f("ix_property_photos_position"))
        batch_op.drop_index(batch_op.f("ix_property_photos_is_cover"))
    op.drop_table("property_photos")

    with op.batch_alter_table("property_feature_values", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_property_feature_values_property_id"))
        batch_op.drop_index(batch_op.f("ix_property_feature_values_attribute_id"))
    op.drop_table("property_feature_values")

    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_properties_status"))
        batch_op.drop_index(batch_op.f("ix_properties_property_type_id"))
        batch_op.drop_index(batch_op.f("ix_properties_owner_user_id"))
        batch_op.drop_index(batch_op.f("ix_properties_name"))
        batch_op.drop_index(batch_op.f("ix_properties_location_address"))
        batch_op.drop_index(batch_op.f("ix_properties_is_published"))
        batch_op.drop_index(batch_op.f("ix_properties_created_at"))
    op.drop_table("properties")

    with op.batch_alter_table("property_type_features", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_property_type_features_slug"))
        batch_op.drop_index(batch_op.f("ix_property_type_features_property_type_id"))
        batch_op.drop_index(batch_op.f("ix_property_type_features_display_order"))
        batch_op.drop_index(batch_op.f("ix_property_type_features_attribute_type"))
    op.drop_table("property_type_features")

    with op.batch_alter_table("property_types", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_property_types_slug"))
        batch_op.drop_index(batch_op.f("ix_property_types_name"))
        batch_op.drop_index(batch_op.f("ix_property_types_is_active"))
        batch_op.drop_index(batch_op.f("ix_property_types_display_order"))
    op.drop_table("property_types")
