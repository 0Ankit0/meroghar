"""Celery tasks for rent increment processing.

Implements T198-T199 from tasks.md.
"""

import logging
from datetime import date
from uuid import UUID

from ..core.database import get_db
from ..services.message_service import MessageService
from ..services.rent_increment_service import RentIncrementService
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.check_and_apply_rent_increments")
def check_and_apply_rent_increments():
    """Daily task to check and apply due rent increments.

    Runs daily at midnight to:
    1. Find tenants with due rent increments
    2. Apply automatic increments
    3. Log all actions

    Implements T198 from tasks.md.
    """
    logger.info("Starting daily rent increment check")

    db = next(get_db())
    try:
        service = RentIncrementService(db)

        # Get tenants due for increment
        due_tenants = service.get_tenants_due_for_increment()

        if not due_tenants:
            logger.info("No tenants due for rent increment")
            return {
                "status": "success",
                "processed": 0,
                "message": "No tenants due for increment",
            }

        logger.info(f"Found {len(due_tenants)} tenants due for rent increment")

        applied_count = 0
        errors = []

        for tenant in due_tenants:
            try:
                # Apply increment using system user ID (or admin)
                # In production, use a designated system user UUID
                system_user_id = tenant.property.owner_id  # Use owner as applier

                old_rent = tenant.monthly_rent
                service.apply_rent_increment(
                    tenant=tenant,
                    applied_by=system_user_id,
                    reason="Automatic annual increment",
                )

                logger.info(
                    f"Applied rent increment for tenant {tenant.id}: "
                    f"{old_rent} -> {tenant.monthly_rent}"
                )

                applied_count += 1

                # Send notification to tenant
                try:
                    message_service = MessageService(db)
                    message_service.send_rent_increment_notification(
                        tenant_id=tenant.id,
                        old_rent=float(old_rent),
                        new_rent=float(tenant.monthly_rent),
                        effective_date=date.today(),
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification for tenant {tenant.id}: {e}")

            except Exception as e:
                error_msg = f"Error applying increment for tenant {tenant.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        result = {
            "status": "completed",
            "processed": applied_count,
            "errors": errors,
        }

        logger.info(f"Rent increment check completed: {applied_count} applied")
        return result

    except Exception as e:
        logger.error(f"Error in rent increment task: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        db.close()


@celery_app.task(name="tasks.send_rent_increment_notifications")
def send_rent_increment_notifications(days_ahead: int = 30):
    """Send notifications for upcoming rent increments.

    Notifies tenants 30 days before scheduled rent increments.

    Implements T199 from tasks.md.

    Args:
        days_ahead: Number of days to look ahead for notifications
    """
    logger.info(f"Checking for rent increments in next {days_ahead} days")

    db = next(get_db())
    try:
        service = RentIncrementService(db)
        message_service = MessageService(db)

        # Get upcoming increments
        upcoming = service.get_upcoming_increments(days_ahead=days_ahead)

        if not upcoming:
            logger.info("No upcoming rent increments to notify")
            return {
                "status": "success",
                "notifications_sent": 0,
            }

        logger.info(f"Found {len(upcoming)} upcoming rent increments")

        sent_count = 0
        errors = []

        for increment_info in upcoming:
            try:
                # Only send if within notification window (e.g., exactly 30 days out)
                if increment_info["days_until"] == days_ahead:
                    message_service.send_upcoming_rent_increment_notification(
                        tenant_id=UUID(str(increment_info["tenant_id"])),
                        current_rent=increment_info["current_rent"],
                        new_rent=increment_info["new_rent"],
                        effective_date=date.fromisoformat(increment_info["increment_date"]),
                    )
                    sent_count += 1
                    logger.info(
                        f"Sent increment notification to tenant {increment_info['tenant_id']}"
                    )

            except Exception as e:
                error_msg = (
                    f"Error sending notification to tenant {increment_info['tenant_id']}: {str(e)}"
                )
                logger.error(error_msg)
                errors.append(error_msg)

        result = {
            "status": "completed",
            "notifications_sent": sent_count,
            "errors": errors,
        }

        logger.info(f"Rent increment notifications completed: {sent_count} sent")
        return result

    except Exception as e:
        logger.error(f"Error in notification task: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        db.close()
