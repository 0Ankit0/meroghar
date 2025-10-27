"""
Celery application configuration.
Implements T022 from tasks.md.
"""

import logging

from celery import Celery
from celery.schedules import crontab

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create Celery application
celery_app = Celery(
    "meroghar",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    # Daily rent increment check at midnight
    "check-rent-increments": {
        "task": "src.tasks.rent_tasks.check_rent_increments",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
    },
    # Document expiration check daily at 9 AM
    "check-document-expirations": {
        "task": "src.tasks.document_tasks.check_document_expirations",
        "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    # Auto-generate recurring bills on 1st of each month
    "generate-recurring-bills": {
        "task": "src.tasks.bill_tasks.generate_recurring_bills",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),  # 1st of month at midnight
    },
    # Send payment reminders at 10 AM daily
    "send-payment-reminders": {
        "task": "src.tasks.notification_tasks.send_payment_reminders",
        "schedule": crontab(hour=10, minute=0),  # Daily at 10 AM
    },
    # Cleanup old sync logs weekly
    "cleanup-old-sync-logs": {
        "task": "src.tasks.maintenance_tasks.cleanup_old_sync_logs",
        "schedule": crontab(day_of_week=0, hour=2, minute=0),  # Sunday at 2 AM
    },
}

logger.info(
    f"Celery configured with broker: {settings.celery_broker_url}, "
    f"backend: {settings.celery_result_backend}"
)


# Task autodiscovery
# celery_app.autodiscover_tasks(['src.tasks'])


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "ok", "task_id": self.request.id}


__all__ = ["celery_app", "debug_task"]
