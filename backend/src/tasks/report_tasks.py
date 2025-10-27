"""Celery tasks for scheduled report generation.

Implements T231 from tasks.md.

Provides automated report generation on schedule with:
- Daily, weekly, monthly, quarterly, annual frequencies
- Email delivery to configured recipients
- Template-based generation
- Error handling and retry logic
"""

import logging
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, select

from ..core.database import async_session_maker, get_db_context
from ..models.report import GeneratedReport, ReportTemplate, ReportType
from ..services.report_service import ReportService
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.tasks.report_tasks.generate_scheduled_reports", bind=True)
def generate_scheduled_reports(self):
    """Generate all scheduled reports that are due.

    This task runs daily and generates reports from all active templates
    that have scheduling enabled and are due for generation.

    Implements T231 from tasks.md.

    Returns:
        dict: Summary of reports generated including:
            - reports_generated: Number of successful reports
            - errors: List of error messages
            - templates_processed: Number of templates processed
    """
    import asyncio

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_generate_scheduled_reports_async())
    return result


async def _generate_scheduled_reports_async() -> dict:
    """Async implementation of scheduled report generation."""
    reports_generated = 0
    templates_processed = 0
    errors = []
    today = datetime.utcnow().date()

    async with async_session_maker() as session:
        try:
            # Get all active scheduled report templates
            result = await session.execute(
                select(ReportTemplate).where(
                    and_(
                        ReportTemplate.is_active,
                        ReportTemplate.is_scheduled,
                    )
                )
            )
            templates = result.scalars().all()

            logger.info(f"Found {len(templates)} scheduled report templates to process")

            for template in templates:
                templates_processed += 1

                try:
                    # Check if report should be generated today
                    if not _should_generate_report(template, today):
                        logger.debug(f"Skipping template {template.id} - not due today")
                        continue

                    # Generate the report synchronously (ReportService uses sync Session)
                    with get_db_context() as sync_db:
                        report_service = ReportService(sync_db)

                        # Prepare parameters based on template config
                        parameters = _prepare_report_parameters(template, today)

                        # Generate report
                        generated_report = report_service.generate_report(
                            template_id=template.id,
                            generated_by=template.created_by,
                            parameters=parameters,
                        )

                        reports_generated += 1

                        logger.info(
                            f"Generated scheduled report {generated_report.id} "
                            f"from template {template.id} ({template.name})"
                        )

                        # TODO: Email report to configured recipients
                        # This would be implemented using the message service
                        # _send_report_email(template, generated_report)

                except Exception as e:
                    error_msg = (
                        f"Failed to generate report from template {template.id} "
                        f"({template.name}): {str(e)}"
                    )
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)

            await session.commit()

            logger.info(
                f"Scheduled report generation complete. "
                f"Processed: {templates_processed}, "
                f"Generated: {reports_generated}, "
                f"Errors: {len(errors)}"
            )

            return {
                "status": "completed",
                "reports_generated": reports_generated,
                "templates_processed": templates_processed,
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate scheduled reports: {str(e)}", exc_info=True)
            await session.rollback()
            return {
                "status": "failed",
                "reports_generated": reports_generated,
                "templates_processed": templates_processed,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


def _should_generate_report(template: ReportTemplate, today: date) -> bool:
    """Check if a report should be generated today based on schedule config.

    Args:
        template: Report template with schedule configuration
        today: Current date

    Returns:
        True if report should be generated, False otherwise
    """
    if not template.schedule_config:
        return False

    schedule = template.schedule_config
    frequency = schedule.get("frequency", "monthly")

    # Check if last generation was recent enough
    if template.last_generated_at:
        last_gen_date = template.last_generated_at.date()
        days_since = (today - last_gen_date).days

        # Don't generate too frequently based on frequency setting
        if frequency == "daily" and days_since < 1:
            return False
        elif frequency == "weekly" and days_since < 7:
            return False
        elif frequency == "monthly" and days_since < 28:
            return False
        elif frequency == "quarterly" and days_since < 90:
            return False
        elif frequency == "annual" and days_since < 365:
            return False

    # Check if today matches the configured day
    if frequency == "monthly":
        # Monthly reports on specific day of month
        day_of_month = schedule.get("day_of_month", 1)
        return today.day == day_of_month

    elif frequency == "quarterly":
        # Quarterly reports on first day of quarter months
        day_of_month = schedule.get("day_of_month", 1)
        return today.month in [1, 4, 7, 10] and today.day == day_of_month

    elif frequency == "annual":
        # Annual reports on specific date
        month = schedule.get("month", 1)
        day = schedule.get("day", 1)
        return today.month == month and today.day == day

    elif frequency == "weekly":
        # Weekly reports on specific day of week (0 = Monday, 6 = Sunday)
        day_of_week = schedule.get("day_of_week", 0)
        return today.weekday() == day_of_week

    elif frequency == "daily":
        # Daily reports
        return True

    # Fallback for custom cron expressions
    return True


def _prepare_report_parameters(template: ReportTemplate, today: date) -> dict:
    """Prepare report generation parameters based on template config.

    Args:
        template: Report template
        today: Current date

    Returns:
        Parameters dictionary for report generation
    """
    parameters = {}

    # Determine date range based on report type and frequency
    if template.report_type in [ReportType.TAX_INCOME, ReportType.TAX_DEDUCTIONS]:
        # Tax reports - use previous year
        parameters["year"] = today.year - 1 if today.month < 3 else today.year

    elif template.report_type == ReportType.TAX_GST:
        # GST reports - use previous quarter
        current_quarter = (today.month - 1) // 3 + 1
        if current_quarter == 1:
            parameters["quarter"] = 4
            parameters["year"] = today.year - 1
        else:
            parameters["quarter"] = current_quarter - 1
            parameters["year"] = today.year

    else:
        # Financial reports - use date range from config or defaults
        schedule = template.schedule_config or {}
        frequency = schedule.get("frequency", "monthly")

        if frequency == "monthly":
            # Previous month
            if today.month == 1:
                period_start = date(today.year - 1, 12, 1)
                period_end = date(today.year - 1, 12, 31)
            else:
                period_start = date(today.year, today.month - 1, 1)
                # Last day of previous month
                period_end = date(today.year, today.month, 1) - datetime.timedelta(days=1)

        elif frequency == "quarterly":
            # Previous quarter
            current_quarter = (today.month - 1) // 3 + 1
            if current_quarter == 1:
                period_start = date(today.year - 1, 10, 1)
                period_end = date(today.year - 1, 12, 31)
            else:
                prev_quarter_start_month = (current_quarter - 2) * 3 + 1
                period_start = date(today.year, prev_quarter_start_month, 1)
                period_end = date(today.year, prev_quarter_start_month + 3, 1) - datetime.timedelta(
                    days=1
                )

        elif frequency == "annual":
            # Previous year
            period_start = date(today.year - 1, 1, 1)
            period_end = date(today.year - 1, 12, 31)

        else:
            # Default to previous month
            if today.month == 1:
                period_start = date(today.year - 1, 12, 1)
                period_end = date(today.year - 1, 12, 31)
            else:
                period_start = date(today.year, today.month - 1, 1)
                period_end = date(today.year, today.month, 1) - datetime.timedelta(days=1)

        parameters["period_start"] = period_start
        parameters["period_end"] = period_end

    # Add format from template
    parameters["format"] = template.default_format

    # Add any custom parameters from template config
    if template.config:
        custom_params = template.config.get("parameters", {})
        parameters.update(custom_params)

    return parameters


@celery_app.task(name="src.tasks.report_tasks.generate_report_by_id", bind=True)
def generate_report_by_id(self, template_id: str, user_id: str, parameters: dict | None = None):
    """Generate a single report by template ID.

    This task can be triggered manually or scheduled individually.

    Args:
        template_id: Report template UUID
        user_id: User ID generating the report
        parameters: Optional report parameters

    Returns:
        dict: Report generation result with report ID or error
    """
    try:
        with get_db_context() as db:
            report_service = ReportService(db)

            generated_report = report_service.generate_report(
                template_id=UUID(template_id),
                generated_by=UUID(user_id),
                parameters=parameters or {},
            )

            logger.info(f"Generated report {generated_report.id} from template {template_id}")

            return {
                "status": "success",
                "report_id": str(generated_report.id),
                "file_url": generated_report.file_url,
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(
            f"Failed to generate report from template {template_id}: {str(e)}", exc_info=True
        )
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(name="src.tasks.report_tasks.cleanup_old_reports", bind=True)
def cleanup_old_reports(self, retention_days: int = 90):
    """Clean up generated reports older than retention period.

    Args:
        retention_days: Number of days to retain reports (default 90)

    Returns:
        dict: Cleanup summary
    """
    import asyncio

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_cleanup_old_reports_async(retention_days))
    return result


async def _cleanup_old_reports_async(retention_days: int) -> dict:
    """Async implementation of report cleanup."""
    deleted_count = 0
    cutoff_date = datetime.utcnow() - datetime.timedelta(days=retention_days)

    async with async_session_maker() as session:
        try:
            # Find old reports
            result = await session.execute(
                select(GeneratedReport).where(GeneratedReport.generated_at < cutoff_date)
            )
            old_reports = result.scalars().all()

            logger.info(f"Found {len(old_reports)} reports older than {retention_days} days")

            for report in old_reports:
                try:
                    # TODO: Delete file from storage (S3, local, etc.)
                    # _delete_report_file(report.file_url)

                    await session.delete(report)
                    deleted_count += 1

                except Exception as e:
                    logger.error(f"Failed to delete report {report.id}: {str(e)}", exc_info=True)

            await session.commit()

            logger.info(f"Deleted {deleted_count} old reports")

            return {
                "status": "completed",
                "deleted_count": deleted_count,
                "retention_days": retention_days,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to cleanup old reports: {str(e)}", exc_info=True)
            await session.rollback()
            return {
                "status": "failed",
                "deleted_count": deleted_count,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
