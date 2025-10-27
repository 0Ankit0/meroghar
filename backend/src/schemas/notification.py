"""Notification request/response schemas.

Implements T237 from tasks.md.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..models.notification import NotificationPriority, NotificationType


# ==================== Request Schemas ====================


class NotificationCreateRequest(BaseModel):
    """Create notification request."""
    
    user_id: int = Field(..., description="Target user ID")
    title: str = Field(
        ..., min_length=1, max_length=255, description="Notification title"
    )
    body: str = Field(..., min_length=1, description="Notification body text")
    notification_type: NotificationType = Field(
        ..., description="Type of notification"
    )
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL, description="Notification priority"
    )
    deep_link: Optional[str] = Field(
        None, max_length=500, description="Deep link for navigation"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata as JSON"
    )


class NotificationMarkReadRequest(BaseModel):
    """Mark notification(s) as read request."""
    
    notification_ids: List[int] = Field(
        ..., min_items=1, description="List of notification IDs to mark as read"
    )


class NotificationUpdateFCMRequest(BaseModel):
    """Update FCM token for user."""
    
    fcm_token: str = Field(..., min_length=1, description="FCM device token")


class NotificationFilterRequest(BaseModel):
    """Filter notifications request."""
    
    notification_type: Optional[NotificationType] = Field(
        None, description="Filter by notification type"
    )
    priority: Optional[NotificationPriority] = Field(
        None, description="Filter by priority"
    )
    is_read: Optional[bool] = Field(
        None, description="Filter by read status"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


# ==================== Response Schemas ====================


class NotificationResponse(BaseModel):
    """Single notification response."""
    
    id: int
    user_id: int
    title: str
    body: str
    notification_type: NotificationType
    priority: NotificationPriority
    deep_link: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    fcm_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivery_failed: bool
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""
    
    notifications: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class NotificationUnreadCountResponse(BaseModel):
    """Unread notification count response."""
    
    unread_count: int
    by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by notification type"
    )
    by_priority: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by priority"
    )


class NotificationBatchResponse(BaseModel):
    """Batch operation response."""
    
    success_count: int
    failed_count: int
    failed_ids: List[int] = Field(default_factory=list)
    message: str
