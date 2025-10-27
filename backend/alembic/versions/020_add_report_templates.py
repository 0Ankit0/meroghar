"""add report template tables

Revision ID: 020_add_report_templates
Revises: 019_add_language_preference
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

Implements T223 from tasks.md.

Creates tables for:
- report_templates: Customizable report templates with configuration
- generated_reports: Generated report instances with file references
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = '020_add_report_templates'
down_revision = '019_add_language_preference'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create report template tables."""
    
    # Create report_type enum
    op.execute("""
        CREATE TYPE report_type AS ENUM (
            'tax_income', 'tax_deductions', 'tax_gst',
            'profit_loss', 'cash_flow', 'balance_sheet',
            'rent_collection', 'expense_breakdown', 'occupancy',
            'custom'
        )
    """)
    
    # Create report_format enum
    op.execute("""
        CREATE TYPE report_format AS ENUM ('pdf', 'excel', 'csv', 'json')
    """)
    
    # Create report_templates table
    op.create_table(
        'report_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', sa.Enum(name='report_type'), nullable=False),
        sa.Column('config', JSON, nullable=False, server_default='{}'),
        sa.Column('is_scheduled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('schedule_config', JSON, nullable=True),
        sa.Column('default_format', sa.Enum(name='report_format'), nullable=False, server_default='pdf'),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_generated_at', sa.DateTime(), nullable=True),
    )
    
    # Create indexes on report_templates
    op.create_index('ix_report_templates_id', 'report_templates', ['id'])
    op.create_index('ix_report_templates_report_type', 'report_templates', ['report_type'])
    op.create_index('ix_report_templates_created_by', 'report_templates', ['created_by'])
    op.create_index('ix_report_templates_is_active', 'report_templates', ['is_active'])
    
    # Create generated_reports table
    op.create_table(
        'generated_reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('template_id', UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('report_type', sa.Enum(name='report_type'), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),
        sa.Column('file_url', sa.String(500), nullable=False),
        sa.Column('file_format', sa.Enum(name='report_format'), nullable=False),
        sa.Column('file_size', sa.String(50), nullable=True),
        sa.Column('generated_by', UUID(as_uuid=True), nullable=False),
        sa.Column('parameters', JSON, nullable=True),
        sa.Column('share_token', sa.String(100), nullable=True, unique=True),
        sa.Column('share_expires_at', sa.DateTime(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('accessed_at', sa.DateTime(), nullable=True),
    )
    
    # Create indexes on generated_reports
    op.create_index('ix_generated_reports_id', 'generated_reports', ['id'])
    op.create_index('ix_generated_reports_report_type', 'generated_reports', ['report_type'])
    op.create_index('ix_generated_reports_generated_by', 'generated_reports', ['generated_by'])
    op.create_index('ix_generated_reports_generated_at', 'generated_reports', ['generated_at'])
    op.create_index('ix_generated_reports_template_id', 'generated_reports', ['template_id'])
    
    # Create foreign keys
    op.create_foreign_key(
        'fk_report_templates_created_by_users',
        'report_templates', 'users',
        ['created_by'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_generated_reports_template_id_report_templates',
        'generated_reports', 'report_templates',
        ['template_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_generated_reports_generated_by_users',
        'generated_reports', 'users',
        ['generated_by'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Drop report template tables."""
    # Drop foreign keys
    op.drop_constraint('fk_generated_reports_generated_by_users', 'generated_reports', type_='foreignkey')
    op.drop_constraint('fk_generated_reports_template_id_report_templates', 'generated_reports', type_='foreignkey')
    op.drop_constraint('fk_report_templates_created_by_users', 'report_templates', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_generated_reports_template_id', 'generated_reports')
    op.drop_index('ix_generated_reports_generated_at', 'generated_reports')
    op.drop_index('ix_generated_reports_generated_by', 'generated_reports')
    op.drop_index('ix_generated_reports_report_type', 'generated_reports')
    op.drop_index('ix_generated_reports_id', 'generated_reports')
    
    op.drop_index('ix_report_templates_is_active', 'report_templates')
    op.drop_index('ix_report_templates_created_by', 'report_templates')
    op.drop_index('ix_report_templates_report_type', 'report_templates')
    op.drop_index('ix_report_templates_id', 'report_templates')
    
    # Drop tables
    op.drop_table('generated_reports')
    op.drop_table('report_templates')
    
    # Drop enums
    op.execute('DROP TYPE report_format')
    op.execute('DROP TYPE report_type')
