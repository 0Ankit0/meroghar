"""
Celery tasks for scheduled message delivery and automatic reminders.

Implements T166-T167 from tasks.md.
"""

from datetime import datetime, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import and_, or_, select

from ..core.database import get_async_session
from ..models.bill import Bill, BillStatus
from ..models.message import Message, MessageStatus
from ..models.tenant import Tenant
from ..schemas.message import MessageChannel, MessageTemplate
from ..services.message_service import MessageService

logger = get_task_logger(__name__)


@shared_task(name="tasks.send_scheduled_messages")
def send_scheduled_messages():
    """
    Send messages that are scheduled for delivery.

    Runs every minute via Celery beat.
    Finds all messages with status=scheduled and scheduled_at <= now.
    """
    import asyncio

    async def async_send():
        async for session in get_async_session():
            try:
                # Find scheduled messages ready to send
                result = await session.execute(
                    select(Message)
                    .where(
                        and_(
                            Message.status == MessageStatus.SCHEDULED,
                            Message.scheduled_at <= datetime.utcnow(),
                        )
                    )
                    .limit(100)  # Process in batches
                )
                messages = result.scalars().all()

                if not messages:
                    logger.info("No scheduled messages to send")
                    return

                logger.info(f"Found {len(messages)} scheduled messages to send")

                # Initialize message service
                message_service = MessageService()

                # Send each message
                sent_count = 0
                failed_count = 0

                for message in messages:
                    try:
                        await message_service.send_message(session, message.id)
                        sent_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send message {message.id}: {str(e)}")
                        failed_count += 1

                logger.info(f"Sent {sent_count} messages, {failed_count} failed")

            except Exception as e:
                logger.error(f"Error in send_scheduled_messages: {str(e)}")
                await session.rollback()
            finally:
                await session.close()

    asyncio.run(async_send())


@shared_task(name="tasks.send_payment_reminders")
def send_payment_reminders():
    """
    Automatically send payment reminders for overdue bills.

    Runs daily at 9 AM via Celery beat.
    Finds tenants with:
    - Bills with status=unpaid or partially_paid
    - Due date within the last 3 days (grace period expired)
    - No payment reminder sent in the last 24 hours
    """
    import asyncio

    async def async_remind():
        async for session in get_async_session():
            try:
                # Calculate date ranges
                now = datetime.utcnow()
                grace_period_cutoff = now - timedelta(days=3)  # 3 days past due
                last_reminder_cutoff = now - timedelta(hours=24)  # No reminder in last 24h

                # Find tenants with overdue bills
                result = await session.execute(
                    select(Tenant)
                    .join(Bill, Bill.tenant_id == Tenant.id)
                    .where(
                        and_(
                            Bill.status.in_([BillStatus.UNPAID, BillStatus.PARTIALLY_PAID]),
                            Bill.due_date <= grace_period_cutoff,
                            # Check for recent reminders
                            or_(
                                ~Tenant.id.in_(
                                    select(Message.tenant_id).where(
                                        and_(
                                            Message.template == MessageTemplate.PAYMENT_OVERDUE,
                                            Message.created_at >= last_reminder_cutoff,
                                        )
                                    )
                                ),
                                True,
                            ),
                        )
                    )
                    .distinct()
                )
                tenants = result.scalars().all()

                if not tenants:
                    logger.info("No tenants requiring payment reminders")
                    return

                logger.info(f"Found {len(tenants)} tenants requiring payment reminders")

                # Create messages for each tenant
                message_service = MessageService()
                sent_count = 0

                for tenant in tenants:
                    try:
                        # Verify tenant has phone number
                        if not tenant.user or not tenant.user.phone:
                            logger.warning(f"Tenant {tenant.id} has no phone number, skipping")
                            continue

                        # Get tenant variables
                        variables = await message_service.get_tenant_variables(session, tenant.id)

                        # Create overdue payment message
                        content = message_service._format_message(
                            template=MessageTemplate.PAYMENT_OVERDUE,
                            channel=MessageChannel.SMS,
                            variables=variables,
                        )

                        message = Message(
                            tenant_id=tenant.id,
                            sent_by=None,  # System-generated
                            property_id=tenant.property_id,
                            template=MessageTemplate.PAYMENT_OVERDUE,
                            content=content,
                            channel=MessageChannel.SMS,
                            recipient_phone=tenant.user.phone,
                            status=MessageStatus.PENDING,
                        )

                        session.add(message)
                        await session.commit()
                        await session.refresh(message)

                        # Send immediately
                        await message_service.send_message(session, message.id)
                        sent_count += 1

                    except Exception as e:
                        logger.error(f"Failed to send reminder to tenant {tenant.id}: {str(e)}")
                        await session.rollback()
                        continue

                logger.info(f"Sent {sent_count} automatic payment reminders")

            except Exception as e:
                logger.error(f"Error in send_payment_reminders: {str(e)}")
                await session.rollback()
            finally:
                await session.close()

    asyncio.run(async_remind())


@shared_task(name="tasks.send_lease_expiry_reminders")
def send_lease_expiry_reminders():
    """
    Send lease expiry reminders to tenants.

    Runs daily at 10 AM via Celery beat.
    Finds tenants with:
    - Lease ending in 30 days or 7 days
    - No expiry reminder sent for this lease period
    """
    import asyncio

    async def async_remind():
        async for session in get_async_session():
            try:
                # Calculate date ranges
                now = datetime.utcnow()
                thirty_days = now + timedelta(days=30)
                seven_days = now + timedelta(days=7)

                # Find tenants with leases expiring soon
                result = await session.execute(
                    select(Tenant).where(
                        or_(
                            and_(
                                Tenant.lease_end_date <= thirty_days,
                                Tenant.lease_end_date >= thirty_days - timedelta(days=1),
                            ),
                            and_(
                                Tenant.lease_end_date <= seven_days,
                                Tenant.lease_end_date >= seven_days - timedelta(days=1),
                            ),
                        )
                    )
                )
                tenants = result.scalars().all()

                if not tenants:
                    logger.info("No tenants with expiring leases")
                    return

                logger.info(f"Found {len(tenants)} tenants with expiring leases")

                # Create messages for each tenant
                message_service = MessageService()
                sent_count = 0

                for tenant in tenants:
                    try:
                        # Verify tenant has phone number
                        if not tenant.user or not tenant.user.phone:
                            logger.warning(f"Tenant {tenant.id} has no phone number, skipping")
                            continue

                        # Check if reminder already sent for this period
                        recent_reminder = await session.execute(
                            select(Message)
                            .where(
                                and_(
                                    Message.tenant_id == tenant.id,
                                    Message.template == MessageTemplate.LEASE_EXPIRING,
                                    Message.created_at >= now - timedelta(days=2),
                                )
                            )
                            .limit(1)
                        )
                        if recent_reminder.scalar_one_or_none():
                            continue

                        # Get tenant variables
                        variables = await message_service.get_tenant_variables(session, tenant.id)

                        # Create lease expiry message
                        content = message_service._format_message(
                            template=MessageTemplate.LEASE_EXPIRING,
                            channel=MessageChannel.SMS,
                            variables=variables,
                        )

                        message = Message(
                            tenant_id=tenant.id,
                            sent_by=None,  # System-generated
                            property_id=tenant.property_id,
                            template=MessageTemplate.LEASE_EXPIRING,
                            content=content,
                            channel=MessageChannel.SMS,
                            recipient_phone=tenant.user.phone,
                            status=MessageStatus.PENDING,
                        )

                        session.add(message)
                        await session.commit()
                        await session.refresh(message)

                        # Send immediately
                        await message_service.send_message(session, message.id)
                        sent_count += 1

                    except Exception as e:
                        logger.error(
                            f"Failed to send lease reminder to tenant {tenant.id}: {str(e)}"
                        )
                        await session.rollback()
                        continue

                logger.info(f"Sent {sent_count} automatic lease expiry reminders")

            except Exception as e:
                logger.error(f"Error in send_lease_expiry_reminders: {str(e)}")
                await session.rollback()
            finally:
                await session.close()

    asyncio.run(async_remind())
