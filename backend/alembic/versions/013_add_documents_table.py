"""Add documents table for file storage

Revision ID: 013
Revises: 012
Create Date: 2025-01-26 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create documents table with enums and indexes."""
    
    # Create document_type enum
    op.execute("""
        CREATE TYPE document_type AS ENUM (
            'lease_agreement',
            'id_proof',
            'income_proof',
            'police_verification',
            'rent_receipt',
            'maintenance_bill',
            'property_deed',
            'tax_receipt',
            'insurance_policy',
            'other'
        )
    """)
    
    # Create document_status enum
    op.execute("""
        CREATE TYPE document_status AS ENUM (
            'active',
            'expired',
            'archived',
            'deleted'
        )
    """)
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('document_type', sa.Enum(
            'lease_agreement', 'id_proof', 'income_proof', 'police_verification',
            'rent_receipt', 'maintenance_bill', 'property_deed', 'tax_receipt',
            'insurance_policy', 'other',
            name='document_type',
            create_type=False
        ), nullable=False),
        sa.Column('status', sa.Enum(
            'active', 'expired', 'archived', 'deleted',
            name='document_status',
            create_type=False
        ), nullable=False, server_default='active'),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('storage_key', sa.String(length=500), nullable=False),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reminder_days_before', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_document_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['parent_document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('storage_key')
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_documents_expiration', 'documents', ['expiration_date', 'status'])
    op.create_index('idx_documents_tenant_type', 'documents', ['tenant_id', 'document_type'])
    op.create_index('idx_documents_property_type', 'documents', ['property_id', 'document_type'])
    op.create_index('idx_documents_uploaded_by', 'documents', ['uploaded_by'])
    op.create_index('idx_documents_parent', 'documents', ['parent_document_id'])
    op.create_index('idx_documents_storage_key', 'documents', ['storage_key'])


def downgrade() -> None:
    """Drop documents table and enums."""
    
    # Drop indexes
    op.drop_index('idx_documents_storage_key', table_name='documents')
    op.drop_index('idx_documents_parent', table_name='documents')
    op.drop_index('idx_documents_uploaded_by', table_name='documents')
    op.drop_index('idx_documents_property_type', table_name='documents')
    op.drop_index('idx_documents_tenant_type', table_name='documents')
    op.drop_index('idx_documents_expiration', table_name='documents')
    
    # Drop table
    op.drop_table('documents')
    
    # Drop enums
    op.execute('DROP TYPE document_status')
    op.execute('DROP TYPE document_type')
