"""Notification management API endpoints.

Implements T239-T241 from tasks.md.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user, get_db
from ...models.notification import NotificationPriority, NotificationType
from ...models.user import User
from ...schemas.notification import (NotificationBatchResponse,
                                     NotificationCreateRequest,
                                     NotificationListResponse,
                                     NotificationMarkReadRequest,
                                     NotificationResponse,
                                     NotificationUnreadCountResponse,
                                     NotificationUpdateFCMRequest)
from ...services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create notification (admin/system use)",
)
async def create_notification(
    request: NotificationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    """Create a new notification.

    This endpoint is typically used by system/admin functions.
    Most notifications are created automatically by service triggers.

    Args:
        request: Notification creation request
        db: Database session
        current_user: Authenticated user

    Returns:
        Created notification

    Raises:
        HTTPException: If creation fails
    """
    # Only owners/intermediaries can create notifications manually
    if not (current_user.is_owner or current_user.is_intermediary):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and intermediaries can create notifications",
        )

    try:
        notification = await NotificationService.create_notification(
            db=db,
            user_id=request.user_id,
            title=request.title,
            body=request.body,
            notification_type=request.notification_type,
            priority=request.priority,
            deep_link=request.deep_link,
            metadata=request.metadata,
            send_push=True,
        )
        return NotificationResponse.model_validate(notification)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}",
        )


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List user's notifications",
)
async def list_notifications(
    notification_type: NotificationType | None = Query(
        None, description="Filter by notification type"
    ),
    priority: NotificationPriority | None = Query(None, description="Filter by priority"),
    is_read: bool | None = Query(None, description="Filter by read status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    """Get paginated list of notifications for the current user.

    Args:
        notification_type: Optional filter by type
        priority: Optional filter by priority
        is_read: Optional filter by read status
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated notification list
    """
    result = await NotificationService.get_notifications(
        db=db,
        user_id=current_user.id,
        notification_type=notification_type,
        priority=priority,
        is_read=is_read,
        page=page,
        page_size=page_size,
    )

    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in result["notifications"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.patch(
    "/mark-read",
    response_model=NotificationBatchResponse,
    summary="Mark notifications as read",
)
async def mark_notifications_as_read(
    request: NotificationMarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationBatchResponse:
    """Mark one or more notifications as read.

    Args:
        request: List of notification IDs to mark as read
        db: Database session
        current_user: Authenticated user

    Returns:
        Batch operation result
    """
    result = await NotificationService.mark_as_read(
        db=db,
        notification_ids=request.notification_ids,
        user_id=current_user.id,
    )

    return NotificationBatchResponse(
        success_count=result["success_count"],
        failed_count=result["failed_count"],
        failed_ids=[
            nid for nid in request.notification_ids if nid not in range(result["success_count"])
        ],
        message=(
            f"Marked {result['success_count']} notification(s) as read"
            if result["failed_count"] == 0
            else f"Marked {result['success_count']} as read, " f"{result['failed_count']} failed"
        ),
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
    summary="Get unread notification count",
)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCountResponse:
    """Get unread notification count for the current user.

    Includes total count and breakdowns by type and priority.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        Unread count with breakdowns
    """
    result = await NotificationService.get_unread_count(
        db=db,
        user_id=current_user.id,
    )

    return NotificationUnreadCountResponse(
        unread_count=result["unread_count"],
        by_type=result["by_type"],
        by_priority=result["by_priority"],
    )


@router.put(
    "/fcm-token",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update FCM device token",
)
async def update_fcm_token(
    request: NotificationUpdateFCMRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Update user's FCM device token for push notifications.

    Mobile app should call this endpoint when:
    - User logs in
    - FCM token is refreshed
    - Device registration changes

    Args:
        request: FCM token update request
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If update fails
    """
    success = await NotificationService.update_fcm_token(
        db=db,
        user_id=current_user.id,
        fcm_token=request.fcm_token,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update FCM token",
        )
