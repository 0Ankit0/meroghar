"""
Document request and response schemas.

Implements T177 from tasks.md.
"""

from datetime import datetime

from pydantic import BaseModel, Field, validator

from ..models.document import DocumentStatus, DocumentType


class DocumentCreate(BaseModel):
    """Schema for creating a document."""

    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    description: str | None = Field(None, description="Document description")
    document_type: DocumentType = Field(..., description="Type of document")
    expiration_date: datetime | None = Field(None, description="Document expiration date")
    reminder_days_before: int = Field(
        30, ge=1, le=365, description="Days before expiration to send reminder"
    )
    tenant_id: int | None = Field(None, description="Related tenant ID")
    property_id: int | None = Field(None, description="Related property ID")

    @validator("expiration_date")
    def validate_expiration(cls, v):
        """Ensure expiration date is in the future."""
        if v and v <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Lease Agreement - John Doe",
                "description": "One-year lease agreement for Unit 101",
                "document_type": "lease_agreement",
                "expiration_date": "2026-01-26T00:00:00Z",
                "reminder_days_before": 30,
                "tenant_id": 1,
                "property_id": 1,
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response after initiating document upload."""

    upload_url: str = Field(..., description="Presigned URL for file upload")
    storage_key: str = Field(..., description="Storage key to use in DocumentComplete")
    expires_in: int = Field(..., description="Upload URL expiration in seconds")
    max_file_size: int = Field(..., description="Maximum file size in bytes")
    allowed_mime_types: list[str] = Field(..., description="Allowed MIME types")

    class Config:
        json_schema_extra = {
            "example": {
                "upload_url": "https://s3.amazonaws.com/bucket/documents/abc-123?signature=xyz",
                "storage_key": "documents/abc-123.pdf",
                "expires_in": 300,
                "max_file_size": 52428800,
                "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png"],
            }
        }


class DocumentComplete(BaseModel):
    """Schema to complete document upload after file is uploaded."""

    storage_key: str = Field(..., description="Storage key from upload response")
    file_name: str = Field(..., max_length=255, description="Original file name")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: str = Field(..., max_length=100, description="MIME type")

    @validator("file_size")
    def validate_file_size(cls, v):
        """Ensure file size is within limits (50MB)."""
        if v > 52428800:  # 50MB
            raise ValueError("File size exceeds maximum limit of 50MB")
        return v

    @validator("mime_type")
    def validate_mime_type(cls, v):
        """Ensure MIME type is allowed."""
        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        if v not in allowed_types:
            raise ValueError(
                f'MIME type {v} not allowed. Allowed types: {", ".join(allowed_types)}'
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "storage_key": "documents/abc-123.pdf",
                "file_name": "lease_agreement.pdf",
                "file_size": 2048576,
                "mime_type": "application/pdf",
            }
        }


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: int
    title: str
    description: str | None
    document_type: DocumentType
    status: DocumentStatus
    file_url: str
    file_name: str
    file_size: int
    file_size_mb: float
    mime_type: str
    storage_key: str
    expiration_date: datetime | None
    is_expired: bool
    days_until_expiration: int | None
    needs_reminder: bool
    reminder_sent: bool
    reminder_days_before: int
    version: int
    parent_document_id: int | None
    uploaded_by: int
    tenant_id: int | None
    property_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Lease Agreement - John Doe",
                "description": "One-year lease agreement for Unit 101",
                "document_type": "lease_agreement",
                "status": "active",
                "file_url": "https://s3.amazonaws.com/bucket/documents/abc-123.pdf",
                "file_name": "lease_agreement.pdf",
                "file_size": 2048576,
                "file_size_mb": 1.95,
                "mime_type": "application/pdf",
                "storage_key": "documents/abc-123.pdf",
                "expiration_date": "2026-01-26T00:00:00Z",
                "is_expired": False,
                "days_until_expiration": 365,
                "needs_reminder": False,
                "reminder_sent": False,
                "reminder_days_before": 30,
                "version": 1,
                "parent_document_id": None,
                "uploaded_by": 2,
                "tenant_id": 1,
                "property_id": 1,
                "created_at": "2025-01-26T16:00:00Z",
                "updated_at": "2025-01-26T16:00:00Z",
            }
        }


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int

    class Config:
        json_schema_extra = {"example": {"documents": [], "total": 25, "page": 1, "page_size": 10}}


class DocumentUpdateStatus(BaseModel):
    """Schema for updating document status."""

    status: DocumentStatus = Field(..., description="New document status")

    class Config:
        json_schema_extra = {"example": {"status": "archived"}}


class DocumentVersionCreate(BaseModel):
    """Schema for creating a new document version."""

    parent_document_id: int = Field(..., description="ID of document to create version from")
    title: str = Field(..., min_length=1, max_length=255, description="New version title")
    description: str | None = Field(None, description="New version description")
    expiration_date: datetime | None = Field(None, description="New expiration date")
    reminder_days_before: int = Field(30, ge=1, le=365, description="Reminder days")

    @validator("expiration_date")
    def validate_expiration(cls, v):
        """Ensure expiration date is in the future."""
        if v and v <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "parent_document_id": 1,
                "title": "Lease Agreement - John Doe (Renewed)",
                "description": "Renewed one-year lease agreement for Unit 101",
                "expiration_date": "2027-01-26T00:00:00Z",
                "reminder_days_before": 30,
            }
        }


class DocumentDownloadResponse(BaseModel):
    """Response with presigned download URL."""

    download_url: str = Field(..., description="Presigned URL for downloading file")
    expires_in: int = Field(..., description="URL expiration in seconds")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")

    class Config:
        json_schema_extra = {
            "example": {
                "download_url": "https://s3.amazonaws.com/bucket/documents/abc-123.pdf?signature=xyz",
                "expires_in": 900,
                "file_name": "lease_agreement.pdf",
                "file_size": 2048576,
                "mime_type": "application/pdf",
            }
        }
