"""Notification service for push notifications via FCM.

Implements T238 from tasks.md.
"""

import json
import logging
from datetime import datetime
from typing import Any

from firebase_admin import credentials, initialize_app, messaging
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification import (Notification, NotificationPriority,
                                   NotificationType)
from ..models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing push notifications."""

    _fcm_initialized = False

    @classmethod
    def initialize_fcm(cls, credentials_path: str | None = None) -> None:
        """Initialize Firebase Cloud Messaging.

        Args:
            credentials_path: Path to Firebase service account JSON file.
                            If None, uses default credentials from environment.
        """
        if cls._fcm_initialized:
            logger.info("FCM already initialized")
            return

        try:
            if credentials_path:
                cred = credentials.Certificate(credentials_path)
                initialize_app(cred)
            else:
                # Use default credentials from environment
                initialize_app()

            cls._fcm_initialized = True
            logger.info("FCM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FCM: {e}")
            raise

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: int,
        title: str,
        body: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        deep_link: str | None = None,
        metadata: dict[str, Any] | None = None,
        send_push: bool = True,
    ) -> Notification:
        """Create a new notification and optionally send push notification.

        Args:
            db: Database session
            user_id: Target user ID
            title: Notification title
            body: Notification body text
            notification_type: Type of notification
            priority: Notification priority level
            deep_link: Optional deep link for navigation
            metadata: Optional additional metadata
            send_push: Whether to send FCM push notification

        Returns:
            Created Notification object
        """
        # Create notification record
        notification = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            priority=priority,
            deep_link=deep_link,
            metadata=metadata,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # Send push notification if enabled
        if send_push:
            try:
                await NotificationService.send_push_notification(db, notification)
            except Exception as e:
                logger.error(f"Failed to send push notification {notification.id}: {e}")
                notification.delivery_failed = True
                notification.failure_reason = str(e)
                await db.commit()

        return notification

    @staticmethod
    async def send_push_notification(
        db: AsyncSession,
        notification: Notification,
    ) -> str | None:
        """Send FCM push notification to user's device.

        Args:
            db: Database session
            notification: Notification object to send

        Returns:
            FCM message ID if successful, None otherwise
        """
        # Get user's FCM token
        result = await db.execute(select(User.fcm_token).where(User.id == notification.user_id))
        fcm_token = result.scalar_one_or_none()

        if not fcm_token:
            logger.warning(
                f"No FCM token for user {notification.user_id}, "
                f"skipping push for notification {notification.id}"
            )
            return None

        try:
            # Build FCM message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification.title,
                    body=notification.body,
                ),
                data={
                    "notification_id": str(notification.id),
                    "type": notification.notification_type.value,
                    "priority": notification.priority.value,
                    "deep_link": notification.deep_link or "",
                    "metadata": json.dumps(notification.metadata or {}),
                },
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority=(
                        "high"
                        if notification.priority
                        in [NotificationPriority.HIGH, NotificationPriority.URGENT]
                        else "normal"
                    ),
                    notification=messaging.AndroidNotification(
                        channel_id=(
                            "urgent"
                            if notification.priority == NotificationPriority.URGENT
                            else notification.notification_type.value
                        ),
                        priority=(
                            "high"
                            if notification.priority == NotificationPriority.URGENT
                            else "default"
                        ),
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1,
                            content_available=True,
                        )
                    )
                ),
            )

            # Send message
            fcm_message_id = messaging.send(message)

            # Update notification with FCM details
            notification.fcm_message_id = fcm_message_id
            notification.sent_at = datetime.utcnow()
            notification.delivery_failed = False
            notification.failure_reason = None
            await db.commit()

            logger.info(
                f"Push notification {notification.id} sent successfully: " f"{fcm_message_id}"
            )
            return fcm_message_id

        except Exception as e:
            logger.error(f"Failed to send FCM message for notification {notification.id}: {e}")
            notification.delivery_failed = True
            notification.failure_reason = str(e)
            await db.commit()
            return None

    @staticmethod
    async def send_batch_notifications(
        db: AsyncSession,
        user_ids: list[int],
        title: str,
        body: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        deep_link: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send notifications to multiple users.

        Args:
            db: Database session
            user_ids: List of target user IDs
            title: Notification title
            body: Notification body text
            notification_type: Type of notification
            priority: Notification priority level
            deep_link: Optional deep link for navigation
            metadata: Optional additional metadata

        Returns:
            Dict with success_count, failed_count, and failed_user_ids
        """
        success_count = 0
        failed_count = 0
        failed_user_ids = []

        for user_id in user_ids:
            try:
                await NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    priority=priority,
                    deep_link=deep_link,
                    metadata=metadata,
                    send_push=True,
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {e}")
                failed_count += 1
                failed_user_ids.append(user_id)

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_user_ids": failed_user_ids,
        }

    @staticmethod
    async def get_notifications(
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType | None = None,
        priority: NotificationPriority | None = None,
        is_read: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Get paginated list of notifications for a user.

        Args:
            db: Database session
            user_id: User ID to fetch notifications for
            notification_type: Optional filter by notification type
            priority: Optional filter by priority
            is_read: Optional filter by read status
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with notifications list and pagination metadata
        """
        # Build query filters
        filters = [Notification.user_id == user_id]
        if notification_type is not None:
            filters.append(Notification.notification_type == notification_type)
        if priority is not None:
            filters.append(Notification.priority == priority)
        if is_read is not None:
            filters.append(Notification.is_read == is_read)

        # Count total matching notifications
        count_query = select(func.count(Notification.id)).where(and_(*filters))
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Fetch paginated notifications
        offset = (page - 1) * page_size
        query = (
            select(Notification)
            .where(and_(*filters))
            .order_by(desc(Notification.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(query)
        notifications = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size

        return {
            "notifications": notifications,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        notification_ids: list[int],
        user_id: int,
    ) -> dict[str, Any]:
        """Mark notifications as read.

        Args:
            db: Database session
            notification_ids: List of notification IDs to mark as read
            user_id: User ID (for access control)

        Returns:
            Dict with success_count and failed_count
        """
        success_count = 0
        failed_count = 0

        for notification_id in notification_ids:
            result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.id == notification_id,
                        Notification.user_id == user_id,
                    )
                )
            )
            notification = result.scalar_one_or_none()

            if notification:
                notification.mark_as_read()
                success_count += 1
            else:
                failed_count += 1

        await db.commit()

        return {
            "success_count": success_count,
            "failed_count": failed_count,
        }

    @staticmethod
    async def get_unread_count(
        db: AsyncSession,
        user_id: int,
    ) -> dict[str, Any]:
        """Get unread notification count for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dict with unread_count, by_type, and by_priority breakdowns
        """
        # Total unread count
        total_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                not Notification.is_read,
            )
        )
        total_result = await db.execute(total_query)
        unread_count = total_result.scalar_one()

        # Count by type
        by_type_query = (
            select(
                Notification.notification_type,
                func.count(Notification.id).label("count"),
            )
            .where(
                and_(
                    Notification.user_id == user_id,
                    not Notification.is_read,
                )
            )
            .group_by(Notification.notification_type)
        )
        by_type_result = await db.execute(by_type_query)
        by_type = {row[0].value: row[1] for row in by_type_result}

        # Count by priority
        by_priority_query = (
            select(
                Notification.priority,
                func.count(Notification.id).label("count"),
            )
            .where(
                and_(
                    Notification.user_id == user_id,
                    not Notification.is_read,
                )
            )
            .group_by(Notification.priority)
        )
        by_priority_result = await db.execute(by_priority_query)
        by_priority = {row[0].value: row[1] for row in by_priority_result}

        return {
            "unread_count": unread_count,
            "by_type": by_type,
            "by_priority": by_priority,
        }

    @staticmethod
    async def update_fcm_token(
        db: AsyncSession,
        user_id: int,
        fcm_token: str,
    ) -> bool:
        """Update user's FCM device token.

        Args:
            db: Database session
            user_id: User ID
            fcm_token: New FCM device token

        Returns:
            True if successful, False otherwise
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.fcm_token = fcm_token
        await db.commit()

        logger.info(f"Updated FCM token for user {user_id}")
        return True
