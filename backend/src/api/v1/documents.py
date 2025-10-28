"""
Document API endpoints for file storage and management.

Implements T178-T180 from tasks.md.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.document import Document, DocumentStatus, DocumentType
from ...models.property import Property
from ...models.tenant import Tenant
from ...models.user import User
from ...schemas.document import (DocumentComplete, DocumentCreate,
                                 DocumentDownloadResponse,
                                 DocumentListResponse, DocumentResponse,
                                 DocumentUpdateStatus, DocumentUploadResponse,
                                 DocumentVersionCreate)
from ...services.document_service import get_document_service
from ..dependencies import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload-url", response_model=DocumentUploadResponse, status_code=status.HTTP_200_OK)
async def get_upload_url(
    document_request: DocumentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    file_extension: str = Query(..., description="File extension (e.g., 'pdf', 'jpg')"),
    mime_type: str = Query(..., description="MIME type (e.g., 'application/pdf')"),
):
    """
    Generate presigned URL for uploading a document.

    Step 1 of document upload process:
    1. Call this endpoint to get upload URL and storage key
    2. Upload file directly to S3 using the presigned URL
    3. Call POST /documents/complete with storage key to finalize

    Args:
        document_request: Document metadata
        file_extension: File extension without dot (pdf, jpg, png, etc.)
        mime_type: Content type for the file

    Returns:
        - upload_url: Presigned S3 URL (5 minute expiry)
        - storage_key: Key to use in complete request
        - expires_in: URL expiration in seconds
        - max_file_size: Maximum file size in bytes (50MB)
        - allowed_mime_types: List of allowed MIME types
    """
    # Validate tenant/property access if specified
    if document_request.tenant_id:
        result = await session.execute(
            select(Tenant).where(Tenant.id == document_request.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {document_request.tenant_id} not found",
            )

    if document_request.property_id:
        result = await session.execute(
            select(Property).where(Property.id == document_request.property_id)
        )
        property_obj = result.scalar_one_or_none()
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {document_request.property_id} not found",
            )

    # Validate MIME type
    doc_service = get_document_service()
    allowed_mime_types = [
        "application/pdf",
        "image/jpeg",
        "image/jpg",
        "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    if mime_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type {mime_type} not allowed. Allowed types: {', '.join(allowed_mime_types)}",
        )

    # Generate storage key and presigned URL
    storage_key = doc_service.generate_storage_key(file_extension)

    try:
        upload_url = doc_service.get_presigned_upload_url(
            storage_key=storage_key, mime_type=mime_type, expires_in=300  # 5 minutes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return DocumentUploadResponse(
        upload_url=upload_url,
        storage_key=storage_key,
        expires_in=300,
        max_file_size=52428800,  # 50MB
        allowed_mime_types=allowed_mime_types,
    )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def complete_document_upload(
    document_metadata: DocumentCreate,
    document_file: DocumentComplete,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Complete document upload after file is uploaded to S3.

    Step 2 of document upload process (after uploading file to S3).
    Creates database record with file metadata.

    Args:
        document_metadata: Document information from upload-url request
        document_file: File details after S3 upload (storage_key, size, etc.)

    Returns:
        Complete document record with all metadata
    """
    # Validate file size
    if document_file.file_size > 52428800:  # 50MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum limit of 50MB",
        )

    # Get file URL
    doc_service = get_document_service()
    file_url = doc_service.get_document_file_url(document_file.storage_key)

    # Create document record
    document = Document(
        title=document_metadata.title,
        description=document_metadata.description,
        document_type=document_metadata.document_type,
        status=DocumentStatus.ACTIVE,
        file_url=file_url,
        file_name=document_file.file_name,
        file_size=document_file.file_size,
        mime_type=document_file.mime_type,
        storage_key=document_file.storage_key,
        expiration_date=document_metadata.expiration_date,
        reminder_days_before=document_metadata.reminder_days_before,
        uploaded_by=current_user.id,
        tenant_id=document_metadata.tenant_id,
        property_id=document_metadata.property_id,
    )

    session.add(document)
    await session.commit()
    await session.refresh(document)

    return document


@router.get("/{document_id}/download", response_model=DocumentDownloadResponse)
async def get_document_download_url(
    document_id: int = Path(..., description="Document ID"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Generate presigned URL for downloading a document.

    Returns a temporary URL (15 minute expiry) for secure file download.
    User must have access to the document (via tenant, property, or ownership).

    Args:
        document_id: ID of document to download

    Returns:
        - download_url: Presigned S3 URL (15 minute expiry)
        - expires_in: URL expiration in seconds
        - file_name: Original file name
        - file_size: File size in bytes
        - mime_type: Content type
    """
    # Get document
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found"
        )

    # Check access (user must be uploader, tenant user, or property owner/intermediary)
    has_access = False
    if document.uploaded_by == current_user.id:
        has_access = True
    elif document.tenant_id:
        tenant_result = await session.execute(select(Tenant).where(Tenant.id == document.tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        if tenant and tenant.user_id == current_user.id:
            has_access = True
    elif document.property_id:
        property_result = await session.execute(
            select(Property).where(Property.id == document.property_id)
        )
        property_obj = property_result.scalar_one_or_none()
        if property_obj and (
            property_obj.owner_id == current_user.id or property_obj.managed_by == current_user.id
        ):
            has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this document"
        )

    # Generate download URL
    doc_service = get_document_service()
    try:
        download_url = doc_service.get_presigned_download_url(
            storage_key=document.storage_key,
            file_name=document.file_name,
            expires_in=900,  # 15 minutes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return DocumentDownloadResponse(
        download_url=download_url,
        expires_in=900,
        file_name=document.file_name,
        file_size=document.file_size,
        mime_type=document.mime_type,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    document_type: DocumentType | None = Query(None, description="Filter by document type"),
    status_filter: DocumentStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    tenant_id: int | None = Query(None, description="Filter by tenant ID"),
    property_id: int | None = Query(None, description="Filter by property ID"),
    uploaded_by: int | None = Query(None, description="Filter by uploader user ID"),
    expiring_before: datetime | None = Query(
        None, description="Filter documents expiring before date"
    ),
    expiring_after: datetime | None = Query(
        None, description="Filter documents expiring after date"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    List documents with filtering and pagination.

    Returns documents accessible to the current user with optional filters:
    - document_type: Filter by type (lease_agreement, id_proof, etc.)
    - status: Filter by status (active, expired, archived, deleted)
    - tenant_id: Show documents for specific tenant
    - property_id: Show documents for specific property
    - uploaded_by: Show documents uploaded by specific user
    - expiring_before/after: Filter by expiration date range

    Results are paginated and sorted by creation date (newest first).
    """
    # Build query
    query = select(Document)

    # Apply filters
    filters = []

    if document_type:
        filters.append(Document.document_type == document_type)

    if status_filter:
        filters.append(Document.status == status_filter)

    if tenant_id:
        filters.append(Document.tenant_id == tenant_id)

    if property_id:
        filters.append(Document.property_id == property_id)

    if uploaded_by:
        filters.append(Document.uploaded_by == uploaded_by)

    if expiring_before:
        filters.append(Document.expiration_date <= expiring_before)

    if expiring_after:
        filters.append(Document.expiration_date >= expiring_after)

    # Add sophisticated access control filter based on RLS policies and user role
    # Users can see documents based on:
    # 1. Documents they uploaded
    # 2. Documents related to properties they own (if owner)
    # 3. Documents related to properties they manage (if intermediary)
    # 4. Their own tenant documents (if tenant)
    # 5. Documents shared with them explicitly
    
    from ...models.property import Property, PropertyAssignment
    from ...models.tenant import Tenant
    from ...models.user import UserRole
    
    access_filters = [
        Document.uploaded_by == current_user.id,
    ]
    
    # Role-based access control
    if current_user.role == UserRole.OWNER:
        # Owners can see documents for their properties
        access_filters.append(
            Document.property_id.in_(
                select(Property.id).where(Property.owner_id == current_user.id)
            )
        )
    elif current_user.role == UserRole.INTERMEDIARY:
        # Intermediaries can see documents for properties they manage
        access_filters.append(
            Document.property_id.in_(
                select(PropertyAssignment.property_id).where(
                    and_(
                        PropertyAssignment.intermediary_id == current_user.id,
                        PropertyAssignment.is_active == True,
                    )
                )
            )
        )
    elif current_user.role == UserRole.TENANT:
        # Tenants can see their own documents
        access_filters.append(
            Document.tenant_id.in_(
                select(Tenant.id).where(Tenant.user_id == current_user.id)
            )
        )
    
    # Add filter for explicitly shared documents (if sharing metadata exists)
    # Documents can have a 'shared_with' field in metadata listing user IDs
    access_filters.append(
        Document.metadata.contains({'shared_with': [str(current_user.id)]})
    )

    if filters:
        query = query.where(and_(*filters, or_(*access_filters)))
    else:
        query = query.where(or_(*access_filters))

    # Count total
    count_query = select(func.count()).select_from(Document).where(query.whereclause)
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await session.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(documents=documents, total=total, page=page, page_size=page_size)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int = Path(..., description="Document ID"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Get document details by ID.

    Returns full document information including:
    - Metadata (title, description, type, status)
    - File information (URL, name, size, MIME type)
    - Expiration tracking (is_expired, days_until_expiration, needs_reminder)
    - Version history (version, parent_document_id)
    - Relationships (uploaded_by, tenant_id, property_id)
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found"
        )

    # Check access
    has_access = False
    if document.uploaded_by == current_user.id:
        has_access = True
    elif document.tenant_id:
        tenant_result = await session.execute(select(Tenant).where(Tenant.id == document.tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        if tenant and tenant.user_id == current_user.id:
            has_access = True
    elif document.property_id:
        property_result = await session.execute(
            select(Property).where(Property.id == document.property_id)
        )
        property_obj = property_result.scalar_one_or_none()
        if property_obj and (
            property_obj.owner_id == current_user.id or property_obj.managed_by == current_user.id
        ):
            has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this document"
        )

    return document


@router.patch("/{document_id}/status", response_model=DocumentResponse)
async def update_document_status(
    document_id: int = Path(..., description="Document ID"),
    status_update: DocumentUpdateStatus = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Update document status.

    Allows changing status between:
    - active: Document is current and accessible
    - expired: Document has passed expiration date
    - archived: Document is no longer active but preserved
    - deleted: Soft delete (can be restored)

    Only the document uploader can change status.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found"
        )

    # Only uploader can change status
    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the document uploader can change status",
        )

    # Update status
    document.status = status_update.status
    document.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(document)

    return document


@router.post("/versions", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document_version(
    version_request: DocumentVersionCreate,
    document_file: DocumentComplete,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new version of an existing document.

    Creates a new document record with:
    - Incremented version number
    - parent_document_id linking to original
    - New file (must be uploaded to S3 first via upload-url endpoint)
    - Updated expiration date

    The parent document will be automatically archived.

    Process:
    1. Call GET /documents/upload-url to get upload URL
    2. Upload new file to S3
    3. Call this endpoint with parent_document_id and file details
    """
    # Get parent document
    result = await session.execute(
        select(Document).where(Document.id == version_request.parent_document_id)
    )
    parent_document = result.scalar_one_or_none()

    if not parent_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent document {version_request.parent_document_id} not found",
        )

    # Only uploader can create versions
    if parent_document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the document uploader can create versions",
        )

    # Create new version
    doc_service = get_document_service()
    file_url = doc_service.get_document_file_url(document_file.storage_key)

    new_version_data = {
        "title": version_request.title,
        "description": version_request.description,
        "document_type": parent_document.document_type,
        "status": DocumentStatus.ACTIVE,
        "file_url": file_url,
        "file_name": document_file.file_name,
        "file_size": document_file.file_size,
        "mime_type": document_file.mime_type,
        "storage_key": document_file.storage_key,
        "expiration_date": version_request.expiration_date,
        "reminder_days_before": version_request.reminder_days_before,
        "uploaded_by": current_user.id,
        "tenant_id": parent_document.tenant_id,
        "property_id": parent_document.property_id,
    }

    new_document = await doc_service.create_document_version(
        parent_document=parent_document, new_document_data=new_version_data, session=session
    )

    return new_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int = Path(..., description="Document ID"),
    hard_delete: bool = Query(False, description="Permanently delete file from storage"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Delete a document.

    By default performs soft delete (sets status to DELETED).
    If hard_delete=true, also deletes file from S3 storage.

    Only the document uploader can delete documents.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found"
        )

    # Only uploader can delete
    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the document uploader can delete documents",
        )

    if hard_delete:
        # Delete file from storage
        doc_service = get_document_service()
        await doc_service.delete_file(document.storage_key)

        # Delete database record
        await session.delete(document)
    else:
        # Soft delete
        document.status = DocumentStatus.DELETED
        document.updated_at = datetime.utcnow()

    await session.commit()
