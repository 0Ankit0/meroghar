"""
Message API endpoints for bulk SMS/WhatsApp reminders.

Implements T163-T165 from tasks.md.
"""
from typing import List, Annotated, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...models.user import User
from ...models.tenant import Tenant
from ...models.message import Message, MessageStatus, MessageChannel
from ...schemas.message import (
    MessageCreate,
    MessageResponse,
    BulkMessageCreate,
    BulkMessageResponse,
    MessageSchedule,
    MessageStatistics,
)
from ...services.message_service import MessageService
from ..dependencies import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/bulk", response_model=BulkMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_bulk_messages(
    bulk_request: BulkMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Send bulk messages to multiple tenants.
    
    Creates individual message records for each tenant and queues them for delivery.
    Supports SMS, WhatsApp, and Email channels with template-based messaging.
    
    Returns:
        - bulk_message_id: Unique ID for this bulk message batch
        - total_messages: Total messages created
        - successful: Successfully queued messages
        - failed: Failed to create messages
        - messages: List of individual message records
    """
    # Verify user has access to tenants
    result = await session.execute(
        select(Tenant)
        .where(Tenant.id.in_(bulk_request.tenant_ids))
        .options(
            selectinload(Tenant.user),
            selectinload(Tenant.property)
        )
    )
    tenants = result.scalars().all()
    
    if len(tenants) != len(bulk_request.tenant_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more tenants not found"
        )
    
    # Generate bulk message ID
    bulk_message_id = f"bulk-{uuid.uuid4()}"
    
    # Initialize message service
    message_service = MessageService()
    
    # Create messages for each tenant
    messages: List[Message] = []
    successful = 0
    failed = 0
    
    for tenant in tenants:
        try:
            # Get tenant variables for template
            variables = await message_service.get_tenant_variables(session, tenant.id)
            
            # Format message content
            content = message_service._format_message(
                template=bulk_request.template,
                channel=bulk_request.channel,
                variables={**variables, 'content': bulk_request.content}
            )
            
            # Get recipient contact info
            recipient_phone = None
            recipient_email = None
            
            if bulk_request.channel in (MessageChannel.SMS, MessageChannel.WHATSAPP):
                recipient_phone = tenant.user.phone if tenant.user else None
                if not recipient_phone:
                    failed += 1
                    continue
            elif bulk_request.channel == MessageChannel.EMAIL:
                recipient_email = tenant.user.email if tenant.user else None
                if not recipient_email:
                    failed += 1
                    continue
            
            # Create message record
            message = Message(
                tenant_id=tenant.id,
                sent_by=current_user.id,
                property_id=tenant.property_id,
                template=bulk_request.template,
                subject=message_service._get_email_subject(bulk_request.template, variables) if bulk_request.channel == MessageChannel.EMAIL else None,
                content=content,
                channel=bulk_request.channel,
                recipient_phone=recipient_phone,
                recipient_email=recipient_email,
                status=MessageStatus.SCHEDULED if bulk_request.scheduled_at else MessageStatus.PENDING,
                scheduled_at=bulk_request.scheduled_at,
                bulk_message_id=bulk_message_id,
            )
            
            session.add(message)
            messages.append(message)
            successful += 1
            
        except Exception as e:
            failed += 1
            continue
    
    await session.commit()
    
    # Refresh messages to get IDs
    for message in messages:
        await session.refresh(message)
    
    # Send messages immediately if not scheduled
    if not bulk_request.scheduled_at:
        for message in messages:
            try:
                await message_service.send_message(session, message.id)
            except Exception:
                pass  # Continue with other messages
    
    return BulkMessageResponse(
        bulk_message_id=bulk_message_id,
        total_messages=len(bulk_request.tenant_ids),
        successful=successful,
        failed=failed,
        messages=[MessageResponse.from_orm(msg) for msg in messages],
    )


@router.post("/schedule", response_model=BulkMessageResponse, status_code=status.HTTP_201_CREATED)
async def schedule_messages(
    schedule_request: MessageSchedule,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Schedule messages for future delivery.
    
    Creates message records with scheduled delivery time.
    Messages will be sent by the background task at the specified time.
    
    Returns:
        - bulk_message_id: Unique ID for this scheduled batch
        - total_messages: Total messages scheduled
        - successful: Successfully scheduled messages
        - failed: Failed to schedule messages
        - messages: List of scheduled message records
    """
    # Convert to bulk create request with scheduled_at
    bulk_request = BulkMessageCreate(
        tenant_ids=schedule_request.tenant_ids,
        template=schedule_request.template,
        channel=schedule_request.channel,
        content=schedule_request.content,
        scheduled_at=schedule_request.scheduled_at,
    )
    
    return await send_bulk_messages(bulk_request, current_user, session)


@router.get("", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
async def list_messages(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[Optional[int], Query(description="Filter by tenant ID")] = None,
    channel: Annotated[Optional[MessageChannel], Query(description="Filter by channel")] = None,
    status_filter: Annotated[Optional[MessageStatus], Query(alias="status", description="Filter by status")] = None,
    bulk_message_id: Annotated[Optional[str], Query(description="Filter by bulk message ID")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of records")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
):
    """
    Get message history with optional filters.
    
    Returns paginated list of messages sent by the current user.
    Supports filtering by tenant, channel, status, and bulk message ID.
    """
    # Build query
    query = select(Message).where(Message.sent_by == current_user.id)
    
    if tenant_id:
        query = query.where(Message.tenant_id == tenant_id)
    
    if channel:
        query = query.where(Message.channel == channel)
    
    if status_filter:
        query = query.where(Message.status == status_filter)
    
    if bulk_message_id:
        query = query.where(Message.bulk_message_id == bulk_message_id)
    
    # Order by most recent first
    query = query.order_by(Message.created_at.desc())
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await session.execute(query)
    messages = result.scalars().all()
    
    return [MessageResponse.from_orm(msg) for msg in messages]


@router.get("/statistics", response_model=MessageStatistics, status_code=status.HTTP_200_OK)
async def get_message_statistics(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[Optional[datetime], Query(description="Start date for statistics")] = None,
    end_date: Annotated[Optional[datetime], Query(description="End date for statistics")] = None,
):
    """
    Get message delivery statistics.
    
    Returns counts and success rates for messages sent by the current user.
    Optionally filtered by date range.
    """
    # Build base query
    query = select(
        func.count(Message.id).label('total'),
        func.count(func.nullif(Message.status == MessageStatus.SENT, False)).label('sent'),
        func.count(func.nullif(Message.status == MessageStatus.DELIVERED, False)).label('delivered'),
        func.count(func.nullif(Message.status == MessageStatus.FAILED, False)).label('failed'),
        func.count(func.nullif(Message.status.in_([MessageStatus.PENDING, MessageStatus.SCHEDULED]), False)).label('pending'),
    ).where(Message.sent_by == current_user.id)
    
    # Apply date filters
    if start_date:
        query = query.where(Message.created_at >= start_date)
    
    if end_date:
        query = query.where(Message.created_at <= end_date)
    
    # Execute query
    result = await session.execute(query)
    row = result.one()
    
    # Calculate delivery rate
    total = row.total or 0
    delivered = row.delivered or 0
    delivery_rate = (delivered / total * 100) if total > 0 else 0
    
    return MessageStatistics(
        total_messages=total,
        sent=row.sent or 0,
        delivered=delivered,
        failed=row.failed or 0,
        pending=row.pending or 0,
        delivery_rate=round(delivery_rate, 2),
    )


@router.get("/{message_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def get_message(
    message_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get a single message by ID.
    
    Returns full message details including delivery status and provider response.
    """
    result = await session.execute(
        select(Message).where(
            and_(
                Message.id == message_id,
                Message.sent_by == current_user.id
            )
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return MessageResponse.from_orm(message)
