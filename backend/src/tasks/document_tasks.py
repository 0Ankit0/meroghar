"""
Celery tasks for document expiration checking and reminders.

Implements T181-T182 from tasks.md.
"""
from datetime import datetime
from typing import List

from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_session
from ..models.document import Document, DocumentStatus
from ..models.tenant import Tenant
from ..models.message import Message, MessageTemplate, MessageChannel, MessageStatus
from ..services.document_service import get_document_service
from ..services.message_service import MessageService

logger = get_task_logger(__name__)


@shared_task(name="tasks.check_document_expirations")
def check_document_expirations():
    """
    Check for expired documents and update their status.
    
    Runs daily at 9 AM via Celery beat.
    Finds all active documents past their expiration date and marks them as expired.
    """
    import asyncio
    
    async def async_check():
        async for session in get_async_session():
            try:
                doc_service = get_document_service()
                
                # Update expired documents
                expired_count = await doc_service.check_and_update_expired_documents(session)
                
                if expired_count > 0:
                    logger.info(f"Marked {expired_count} documents as expired")
                else:
                    logger.info("No documents to mark as expired")
                
            except Exception as e:
                logger.error(f"Error in check_document_expirations: {str(e)}")
                await session.rollback()
            finally:
                await session.close()
    
    asyncio.run(async_check())


@shared_task(name="tasks.send_document_expiration_reminders")
def send_document_expiration_reminders():
    """
    Send expiration reminders for documents approaching expiration.
    
    Runs daily at 9:30 AM via Celery beat (after check_document_expirations).
    Finds documents within reminder window and sends SMS/WhatsApp notifications.
    Integrates with US8 messaging system.
    """
    import asyncio
    
    async def async_send_reminders():
        async for session in get_async_session():
            try:
                doc_service = get_document_service()
                message_service = MessageService()
                
                # Get documents needing reminders
                documents = await doc_service.get_documents_needing_reminders(session)
                
                if not documents:
                    logger.info("No documents needing expiration reminders")
                    return
                
                logger.info(f"Found {len(documents)} documents needing expiration reminders")
                
                sent_count = 0
                failed_count = 0
                
                for document in documents:
                    try:
                        # Get tenant information if available
                        tenant = None
                        if document.tenant_id:
                            result = await session.execute(
                                select(Tenant).where(Tenant.id == document.tenant_id)
                            )
                            tenant = result.scalar_one_or_none()
                        
                        if not tenant or not tenant.user or not tenant.user.phone:
                            logger.warning(f"Document {document.id} has no valid tenant contact info")
                            continue
                        
                        # Format expiration message
                        days_left = document.days_until_expiration
                        expiry_date = document.expiration_date.strftime("%Y-%m-%d") if document.expiration_date else "soon"
                        
                        content = (
                            f"Hi {tenant.user.name},\n\n"
                            f"Your document '{document.title}' ({document.document_type.value}) "
                            f"will expire on {expiry_date}"
                        )
                        
                        if days_left is not None:
                            content += f" (in {days_left} days)"
                        
                        content += ".\n\nPlease renew or upload a new version to maintain compliance."
                        
                        # Determine channel (prefer WhatsApp for documents, fallback to SMS)
                        channel = MessageChannel.WHATSAPP
                        
                        # Create message record
                        message = Message(
                            tenant_id=tenant.id,
                            sent_by=document.uploaded_by,
                            property_id=document.property_id,
                            template=MessageTemplate.LEASE_EXPIRING,  # Reuse lease_expiring template
                            content=content,
                            channel=channel,
                            recipient_phone=tenant.user.phone,
                            status=MessageStatus.PENDING,
                        )
                        
                        session.add(message)
                        await session.flush()
                        
                        # Send message via message service
                        await message_service.send_message(session, message.id)
                        
                        # Mark reminder as sent
                        await doc_service.mark_reminder_sent(document, session)
                        
                        sent_count += 1
                        logger.info(f"Sent expiration reminder for document {document.id} to tenant {tenant.id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to send reminder for document {document.id}: {str(e)}")
                        failed_count += 1
                
                logger.info(f"Sent {sent_count} document expiration reminders, {failed_count} failed")
                
            except Exception as e:
                logger.error(f"Error in send_document_expiration_reminders: {str(e)}")
                await session.rollback()
            finally:
                await session.close()
    
    asyncio.run(async_send_reminders())


@shared_task(name="tasks.cleanup_deleted_documents")
def cleanup_deleted_documents():
    """
    Clean up documents marked as DELETED after retention period.
    
    Runs weekly on Sunday at 2 AM via Celery beat.
    Permanently deletes documents that have been soft-deleted for 90+ days.
    """
    import asyncio
    from datetime import timedelta
    
    async def async_cleanup():
        async for session in get_async_session():
            try:
                doc_service = get_document_service()
                
                # Find documents deleted more than 90 days ago
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                
                result = await session.execute(
                    select(Document).where(
                        Document.status == DocumentStatus.DELETED,
                        Document.updated_at < cutoff_date
                    )
                )
                documents = result.scalars().all()
                
                if not documents:
                    logger.info("No deleted documents to clean up")
                    return
                
                logger.info(f"Found {len(documents)} deleted documents to clean up")
                
                cleaned_count = 0
                failed_count = 0
                
                for document in documents:
                    try:
                        # Delete file from storage
                        await doc_service.delete_file(document.storage_key)
                        
                        # Delete database record
                        await session.delete(document)
                        
                        cleaned_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to clean up document {document.id}: {str(e)}")
                        failed_count += 1
                
                await session.commit()
                
                logger.info(f"Cleaned up {cleaned_count} deleted documents, {failed_count} failed")
                
            except Exception as e:
                logger.error(f"Error in cleanup_deleted_documents: {str(e)}")
                await session.rollback()
            finally:
                await session.close()
    
    asyncio.run(async_cleanup())
