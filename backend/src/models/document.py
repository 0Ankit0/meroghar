"""
Document model for file storage and management.

Implements T175 from tasks.md.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class DocumentType(str, PyEnum):
    """Document type enumeration."""
    LEASE_AGREEMENT = "lease_agreement"
    ID_PROOF = "id_proof"
    INCOME_PROOF = "income_proof"
    POLICE_VERIFICATION = "police_verification"
    RENT_RECEIPT = "rent_receipt"
    MAINTENANCE_BILL = "maintenance_bill"
    PROPERTY_DEED = "property_deed"
    TAX_RECEIPT = "tax_receipt"
    INSURANCE_POLICY = "insurance_policy"
    OTHER = "other"


class DocumentStatus(str, PyEnum):
    """Document status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Document(Base):
    """
    Document model for storing file references and metadata.
    
    Supports:
    - Multiple document types (lease, ID, receipts, etc.)
    - Expiration tracking with automatic reminders
    - Version history for updated documents
    - Secure access control via RLS
    - S3/cloud storage integration
    """
    __tablename__ = "documents"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Document metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, native_enum=False),
        nullable=False,
        index=True
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False),
        nullable=False,
        default=DocumentStatus.ACTIVE,
        index=True
    )

    # File information
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)

    # Expiration tracking
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    reminder_sent: Mapped[bool] = mapped_column(default=False)
    reminder_days_before: Mapped[int] = mapped_column(Integer, default=30)  # Days before expiration to send reminder

    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_document_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    uploaded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tenant_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    property_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True
    )

    # Relationships
    uploader = relationship("User", foreign_keys=[uploaded_by], back_populates="uploaded_documents")
    tenant = relationship("Tenant", back_populates="documents")
    property = relationship("Property", back_populates="documents")
    parent_document = relationship("Document", remote_side=[id], foreign_keys=[parent_document_id])

    # Indexes
    __table_args__ = (
        Index("idx_documents_expiration", "expiration_date", "status"),
        Index("idx_documents_tenant_type", "tenant_id", "document_type"),
        Index("idx_documents_property_type", "property_id", "document_type"),
    )

    @property
    def is_expired(self) -> bool:
        """Check if document is expired."""
        if not self.expiration_date:
            return False
        return datetime.utcnow() > self.expiration_date

    @property
    def days_until_expiration(self) -> Optional[int]:
        """Calculate days until expiration."""
        if not self.expiration_date:
            return None
        delta = self.expiration_date - datetime.utcnow()
        return delta.days if delta.days >= 0 else 0

    @property
    def needs_reminder(self) -> bool:
        """Check if reminder should be sent."""
        if self.reminder_sent or not self.expiration_date:
            return False
        days_left = self.days_until_expiration
        return days_left is not None and days_left <= self.reminder_days_before

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}', type={self.document_type}, status={self.status})>"
