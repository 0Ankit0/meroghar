"""
Message request and response schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from ..models.message import MessageChannel, MessageStatus, MessageTemplate


class MessageTemplateVariable(BaseModel):
    """Template variable for personalization."""
    
    tenant_name: Optional[str] = None
    property_name: Optional[str] = None
    amount_due: Optional[float] = None
    due_date: Optional[str] = None
    payment_link: Optional[str] = None


class MessageCreate(BaseModel):
    """Schema for creating a single message."""
    
    tenant_id: int = Field(..., description="Recipient tenant ID")
    property_id: Optional[int] = Field(None, description="Related property ID")
    template: MessageTemplate = Field(..., description="Message template")
    channel: MessageChannel = Field(..., description="Delivery channel")
    subject: Optional[str] = Field(None, description="Message subject (for email)")
    content: str = Field(..., description="Message content")
    recipient_phone: Optional[str] = Field(None, description="Phone number")
    recipient_email: Optional[str] = Field(None, description="Email address")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule send time")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": 1,
                "property_id": 1,
                "template": "payment_reminder",
                "channel": "sms",
                "content": "Hi {tenant_name}, your rent of Rs. {amount_due} is due on {due_date}. Please pay at your earliest convenience.",
                "recipient_phone": "+9779812345678",
                "scheduled_at": "2025-01-27T10:00:00Z"
            }
        }


class BulkMessageCreate(BaseModel):
    """Schema for creating bulk messages."""
    
    tenant_ids: List[int] = Field(..., description="List of tenant IDs")
    template: MessageTemplate = Field(..., description="Message template")
    channel: MessageChannel = Field(..., description="Delivery channel")
    subject: Optional[str] = Field(None, description="Message subject (for email)")
    content: str = Field(..., description="Message content with placeholders")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule send time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_ids": [1, 2, 3],
                "template": "payment_overdue",
                "channel": "whatsapp",
                "content": "Dear {tenant_name}, your rent payment of Rs. {amount_due} for {property_name} is overdue. Please pay immediately to avoid late fees.",
                "scheduled_at": None
            }
        }


class MessageSchedule(BaseModel):
    """Schema for scheduling a message."""
    
    tenant_ids: List[int] = Field(..., description="List of tenant IDs")
    template: MessageTemplate = Field(..., description="Message template")
    channel: MessageChannel = Field(..., description="Delivery channel")
    content: str = Field(..., description="Message content")
    scheduled_at: datetime = Field(..., description="Scheduled send time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_ids": [1, 2, 3],
                "template": "payment_reminder",
                "channel": "sms",
                "content": "Rent reminder: Rs. {amount_due} due on {due_date}",
                "scheduled_at": "2025-02-01T09:00:00Z"
            }
        }


class MessageResponse(BaseModel):
    """Schema for message response."""
    
    id: int
    tenant_id: int
    sent_by: int
    property_id: Optional[int]
    template: MessageTemplate
    subject: Optional[str]
    content: str
    channel: MessageChannel
    recipient_phone: Optional[str]
    recipient_email: Optional[str]
    status: MessageStatus
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    provider_message_id: Optional[str]
    bulk_message_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "tenant_id": 1,
                "sent_by": 2,
                "property_id": 1,
                "template": "payment_reminder",
                "subject": None,
                "content": "Hi John, your rent of Rs. 15000 is due on 2025-02-01.",
                "channel": "sms",
                "recipient_phone": "+9779812345678",
                "recipient_email": None,
                "status": "sent",
                "scheduled_at": None,
                "sent_at": "2025-01-26T14:30:00Z",
                "delivered_at": "2025-01-26T14:30:05Z",
                "error_message": None,
                "retry_count": 0,
                "max_retries": 3,
                "provider_message_id": "SM1234567890",
                "bulk_message_id": "bulk-abc-123",
                "created_at": "2025-01-26T14:29:50Z",
                "updated_at": "2025-01-26T14:30:05Z"
            }
        }


class BulkMessageResponse(BaseModel):
    """Response for bulk message operation."""
    
    bulk_message_id: str = Field(..., description="Bulk message batch ID")
    total_messages: int = Field(..., description="Total messages created")
    successful: int = Field(..., description="Successfully queued messages")
    failed: int = Field(..., description="Failed messages")
    messages: List[MessageResponse] = Field(..., description="Individual message details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bulk_message_id": "bulk-abc-123",
                "total_messages": 10,
                "successful": 9,
                "failed": 1,
                "messages": []
            }
        }


class MessageStatistics(BaseModel):
    """Message delivery statistics."""
    
    total_messages: int
    sent: int
    delivered: int
    failed: int
    pending: int
    delivery_rate: float = Field(..., description="Delivery success rate (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_messages": 100,
                "sent": 95,
                "delivered": 90,
                "failed": 5,
                "pending": 0,
                "delivery_rate": 94.7
            }
        }
