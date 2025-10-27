"""add language preference to users table

Revision ID: 019_add_language_preference
Revises: 018_add_notifications_rls_policies
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

Implements T220 from tasks.md.

Adds language_preference column to users table to store user's preferred language
for localization (en, hi, es, ar).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '019_add_language_preference'
down_revision = '018_add_notifications_rls_policies'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add language_preference column to users table."""
    # Add language_preference column with default 'en'
    op.add_column(
        'users',
        sa.Column(
            'language_preference',
            sa.String(length=10),
            nullable=True,
            server_default='en',
            comment="User's preferred language (ISO 639-1 code: en, hi, es, ar)",
        )
    )
    
    # Update existing users to have default language 'en'
    op.execute("UPDATE users SET language_preference = 'en' WHERE language_preference IS NULL")


def downgrade() -> None:
    """Remove language_preference column from users table."""
    op.drop_column('users', 'language_preference')
