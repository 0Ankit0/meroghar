"""Document upload service for S3-compatible storage.

Implements T128, T178-T184 from tasks.md.
Supports AWS S3, MinIO, or local file storage for receipts and documents.
Enhanced with presigned URLs, version history, and expiration tracking.
"""

import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.document import Document, DocumentStatus

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for uploading and managing documents (receipts, contracts, etc.)."""

    def __init__(
        self,
        storage_type: str = "local",
        bucket_name: str | None = None,
        aws_access_key: str | None = None,
        aws_secret_key: str | None = None,
        endpoint_url: str | None = None,
        local_storage_path: str | None = None,
    ):
        """Initialize document service.

        Args:
            storage_type: "s3", "minio", or "local"
            bucket_name: S3 bucket name (for S3/MinIO)
            aws_access_key: AWS access key (for S3/MinIO)
            aws_secret_key: AWS secret key (for S3/MinIO)
            endpoint_url: Custom endpoint URL (for MinIO)
            local_storage_path: Path for local file storage
        """
        self.storage_type = storage_type
        self.bucket_name = bucket_name
        self.local_storage_path = local_storage_path or os.path.join(
            tempfile.gettempdir(), "meroghar_documents"
        )

        # Initialize S3 client if using S3/MinIO
        if storage_type in ["s3", "minio"]:
            try:
                import boto3

                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    endpoint_url=endpoint_url,
                )
                logger.info(f"Initialized {storage_type} storage with bucket: {bucket_name}")
            except ImportError:
                logger.warning(
                    "boto3 not installed. Falling back to local storage. "
                    "Install boto3 to use S3/MinIO storage."
                )
                self.storage_type = "local"
                self.s3_client = None
        else:
            self.s3_client = None
            # Create local storage directory if it doesn't exist
            os.makedirs(self.local_storage_path, exist_ok=True)
            logger.info(f"Initialized local storage at: {self.local_storage_path}")

    async def upload_receipt(
        self,
        file: BinaryIO,
        filename: str,
        expense_id: UUID,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload expense receipt to storage.

        Args:
            file: File-like object containing the receipt
            filename: Original filename
            expense_id: Expense ID this receipt is for
            content_type: MIME type of the file

        Returns:
            URL or path to the uploaded file

        Raises:
            Exception: If upload fails
        """
        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"receipts/{expense_id}/{uuid4()}{file_extension}"

        logger.info(f"Uploading receipt: {unique_filename}")

        if self.storage_type in ["s3", "minio"] and self.s3_client:
            return await self._upload_to_s3(file, unique_filename, content_type)
        else:
            return await self._upload_to_local(file, unique_filename)

    async def upload_document(
        self,
        file: BinaryIO,
        filename: str,
        document_type: str,
        entity_id: UUID,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload general document to storage.

        Args:
            file: File-like object containing the document
            filename: Original filename
            document_type: Type of document (contract, lease, etc.)
            entity_id: ID of entity this document belongs to
            content_type: MIME type of the file

        Returns:
            URL or path to the uploaded file
        """
        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"{document_type}/{entity_id}/{uuid4()}{file_extension}"

        logger.info(f"Uploading document: {unique_filename}")

        if self.storage_type in ["s3", "minio"] and self.s3_client:
            return await self._upload_to_s3(file, unique_filename, content_type)
        else:
            return await self._upload_to_local(file, unique_filename)

    async def _upload_to_s3(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
    ) -> str:
        """Upload file to S3-compatible storage.

        Args:
            file: File-like object
            filename: S3 key (path)
            content_type: MIME type

        Returns:
            S3 URL
        """
        try:
            # Upload to S3
            self.s3_client.upload_fileobj(
                file, self.bucket_name, filename, ExtraArgs={"ContentType": content_type}
            )

            # Generate URL
            if self.storage_type == "minio":
                # For MinIO, construct URL from endpoint
                url = f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{filename}"
            else:
                # For AWS S3
                url = f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"

            logger.info(f"Uploaded to S3: {url}")
            return url

        except Exception as e:
            logger.exception(f"S3 upload failed: {e}")
            raise Exception(f"Failed to upload to S3: {str(e)}")

    async def _upload_to_local(
        self,
        file: BinaryIO,
        filename: str,
    ) -> str:
        """Upload file to local storage.

        Args:
            file: File-like object
            filename: Relative path

        Returns:
            Local file path
        """
        try:
            # Create full path
            full_path = os.path.join(self.local_storage_path, filename)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write file
            with open(full_path, "wb") as f:
                file.seek(0)  # Reset file pointer
                f.write(file.read())

            logger.info(f"Uploaded to local storage: {full_path}")
            return full_path

        except Exception as e:
            logger.exception(f"Local upload failed: {e}")
            raise Exception(f"Failed to upload to local storage: {str(e)}")

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from storage.

        Args:
            file_url: URL or path to the file

        Returns:
            True if deleted successfully
        """
        try:
            if self.storage_type in ["s3", "minio"] and self.s3_client:
                # Extract key from URL
                key = file_url.split(f"{self.bucket_name}/")[-1]
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                logger.info(f"Deleted from S3: {key}")
            else:
                # Delete from local storage
                if os.path.exists(file_url):
                    os.remove(file_url)
                    logger.info(f"Deleted from local storage: {file_url}")

            return True

        except Exception as e:
            logger.exception(f"Failed to delete file: {e}")
            return False

    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for file access (for S3).

        Args:
            file_path: S3 key or local path
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL or local path
        """
        if self.storage_type in ["s3", "minio"] and self.s3_client:
            try:
                # Generate presigned URL
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": file_path},
                    ExpiresIn=expires_in,
                )
                return url
            except Exception as e:
                logger.exception(f"Failed to generate presigned URL: {e}")
                return file_path
        else:
            # For local storage, return the path
            return file_path

    # New methods for Document model support (T178-T184)

    def generate_storage_key(self, file_extension: str) -> str:
        """
        Generate unique storage key for document file.

        Args:
            file_extension: File extension (e.g., 'pdf', 'jpg')

        Returns:
            Storage key in format: documents/{uuid}.{extension}
        """
        unique_id = str(uuid4())
        return f"documents/{unique_id}.{file_extension}"

    def get_presigned_upload_url(
        self, storage_key: str, mime_type: str, expires_in: int = 300
    ) -> str:
        """
        Generate presigned URL for uploading file to S3.

        Args:
            storage_key: S3 object key
            mime_type: Content type for the file
            expires_in: URL expiration in seconds (default 5 minutes)

        Returns:
            Presigned upload URL

        Raises:
            ValueError: If S3 is not configured
            ClientError: If S3 operation fails
        """
        if self.storage_type not in ["s3", "minio"] or not self.s3_client:
            raise ValueError("S3 storage is not configured. Please set AWS credentials.")

        if not self.bucket_name:
            raise ValueError("S3 bucket name is not configured.")

        try:
            url = self.s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": storage_key,
                    "ContentType": mime_type,
                },
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            raise ValueError(f"Failed to generate upload URL: {str(e)}")

    def get_presigned_download_url(
        self, storage_key: str, file_name: str, expires_in: int = 900
    ) -> str:
        """
        Generate presigned URL for downloading file from S3.

        Args:
            storage_key: S3 object key
            file_name: Original file name for Content-Disposition header
            expires_in: URL expiration in seconds (default 15 minutes)

        Returns:
            Presigned download URL

        Raises:
            ValueError: If S3 is not configured
        """
        if self.storage_type not in ["s3", "minio"] or not self.s3_client:
            raise ValueError("S3 storage is not configured. Please set AWS credentials.")

        if not self.bucket_name:
            raise ValueError("S3 bucket name is not configured.")

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": storage_key,
                    "ResponseContentDisposition": f'attachment; filename="{file_name}"',
                },
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            raise ValueError(f"Failed to generate download URL: {str(e)}")

    def get_document_file_url(self, storage_key: str) -> str:
        """
        Get permanent file URL (for public buckets) or construct S3 URL.

        Args:
            storage_key: S3 object key

        Returns:
            S3 object URL or local path
        """
        if self.storage_type in ["s3", "minio"]:
            if not self.bucket_name:
                return ""

            if self.storage_type == "minio":
                # For MinIO, construct URL from endpoint
                return f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{storage_key}"
            else:
                # For AWS S3
                return f"https://{self.bucket_name}.s3.amazonaws.com/{storage_key}"
        else:
            # For local storage
            return os.path.join(self.local_storage_path, storage_key)

    async def get_documents_needing_reminders(self, session: AsyncSession) -> list[Document]:
        """
        Get documents that need expiration reminders.

        Finds documents where:
        - Status is ACTIVE
        - Expiration date is set
        - Reminder not yet sent
        - Current date is within reminder window

        Args:
            session: Database session

        Returns:
            List of documents needing reminders
        """
        result = await session.execute(
            select(Document)
            .where(
                Document.status == DocumentStatus.ACTIVE,
                Document.expiration_date.isnot(None),
                not Document.reminder_sent,
            )
            .limit(100)  # Process in batches
        )
        documents = result.scalars().all()

        # Filter by needs_reminder property
        return [doc for doc in documents if doc.needs_reminder]

    async def mark_reminder_sent(self, document: Document, session: AsyncSession) -> None:
        """
        Mark reminder as sent for a document.

        Args:
            document: Document to update
            session: Database session
        """
        document.reminder_sent = True
        document.updated_at = datetime.utcnow()
        await session.commit()

    async def check_and_update_expired_documents(self, session: AsyncSession) -> int:
        """
        Check for expired documents and update their status.

        Finds documents where:
        - Status is ACTIVE
        - Expiration date is in the past

        Args:
            session: Database session

        Returns:
            Number of documents marked as expired
        """
        result = await session.execute(
            select(Document).where(
                Document.status == DocumentStatus.ACTIVE,
                Document.expiration_date.isnot(None),
                Document.expiration_date < datetime.utcnow(),
            )
        )
        documents = result.scalars().all()

        count = 0
        for doc in documents:
            doc.status = DocumentStatus.EXPIRED
            doc.updated_at = datetime.utcnow()
            count += 1

        if count > 0:
            await session.commit()

        return count

    async def create_document_version(
        self, parent_document: Document, new_document_data: dict[str, Any], session: AsyncSession
    ) -> Document:
        """
        Create a new version of a document.

        Args:
            parent_document: Original document
            new_document_data: Data for new version
            session: Database session

        Returns:
            New document version
        """
        # Create new document with incremented version
        new_document = Document(
            **new_document_data,
            version=parent_document.version + 1,
            parent_document_id=parent_document.id,
        )

        # Archive old version
        parent_document.status = DocumentStatus.ARCHIVED
        parent_document.updated_at = datetime.utcnow()

        session.add(new_document)
        await session.commit()
        await session.refresh(new_document)

        return new_document

    async def revoke_tenant_document_access(self, tenant_id: int, session: AsyncSession) -> int:
        """
        Revoke access to documents when tenant is deactivated.

        Archives all active documents for the tenant.

        Args:
            tenant_id: Tenant ID
            session: Database session

        Returns:
            Number of documents archived
        """
        result = await session.execute(
            select(Document).where(
                Document.tenant_id == tenant_id, Document.status == DocumentStatus.ACTIVE
            )
        )
        documents = result.scalars().all()

        count = 0
        for doc in documents:
            doc.status = DocumentStatus.ARCHIVED
            doc.updated_at = datetime.utcnow()
            count += 1

        if count > 0:
            await session.commit()

        return count

    async def get_document_version_history(
        self, document_id: int, session: AsyncSession
    ) -> list[Document]:
        """
        Get version history for a document.

        Returns all versions (parent and children) for a document.

        Args:
            document_id: Document ID
            session: Database session

        Returns:
            List of documents in version chain
        """
        # Get the document
        result = await session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            return []

        # Find root document
        root_id = document.id
        if document.parent_document_id:
            root_result = await session.execute(
                select(Document.id).where(Document.id == document.parent_document_id)
            )
            root_id = root_result.scalar_one_or_none() or document.id

        # Get all documents in version chain
        result = await session.execute(
            select(Document)
            .where(
                (Document.id == root_id)
                | (Document.parent_document_id == root_id)
                | (Document.parent_document_id == document.id)
            )
            .order_by(Document.version.asc())
        )

        return list(result.scalars().all())


# Singleton instance
_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    """Get or create document service instance.

    Returns:
        DocumentService singleton instance
    """
    global _document_service

    if _document_service is None:
        # Get configuration from environment variables
        storage_type = os.getenv("STORAGE_TYPE", "local")
        bucket_name = os.getenv("S3_BUCKET_NAME")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        endpoint_url = os.getenv("S3_ENDPOINT_URL")  # For MinIO
        local_storage_path = os.getenv("LOCAL_STORAGE_PATH")

        _document_service = DocumentService(
            storage_type=storage_type,
            bucket_name=bucket_name,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            endpoint_url=endpoint_url,
            local_storage_path=local_storage_path,
        )

    return _document_service


__all__ = ["DocumentService", "get_document_service"]
