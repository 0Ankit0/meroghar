"""Document upload service for S3-compatible storage.

Implements T128 from tasks.md.
Supports AWS S3, MinIO, or local file storage for receipts and documents.
"""
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for uploading and managing documents (receipts, contracts, etc.)."""

    def __init__(
        self,
        storage_type: str = "local",
        bucket_name: Optional[str] = None,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        local_storage_path: Optional[str] = None,
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
                    's3',
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
                file,
                self.bucket_name,
                filename,
                ExtraArgs={'ContentType': content_type}
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
            with open(full_path, 'wb') as f:
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
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_path},
                    ExpiresIn=expires_in
                )
                return url
            except Exception as e:
                logger.exception(f"Failed to generate presigned URL: {e}")
                return file_path
        else:
            # For local storage, return the path
            return file_path


# Singleton instance
_document_service: Optional[DocumentService] = None


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
