"""Celery tasks for notification management.

Implements T122 from tasks.md.
"""

import logging
from uuid import UUID

from sqlalchemy import select

from ..core.database import async_session_maker
from ..models.payment import Payment, PaymentStatus
from ..models.tenant import Tenant
from ..models.user import User
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.tasks.notification_tasks.send_payment_confirmation", bind=True)
def send_payment_confirmation(self, payment_id: str):
    """Send payment confirmation notification to tenant.

    This task is called automatically after a successful payment gateway transaction.
    It sends an email/SMS/push notification to the tenant confirming the payment.

    Args:
        payment_id: UUID of the completed payment

    Returns:
        dict: Notification status and details
    """
    import asyncio

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_send_payment_confirmation_async(UUID(payment_id)))
    return result


async def _send_payment_confirmation_async(payment_id: UUID) -> dict[str, any]:
    """Async implementation of payment confirmation notification.

    Args:
        payment_id: Payment ID

    Returns:
        dict: Status, channels used, and any errors
    """
    notifications_sent = []
    errors = []

    async with async_session_maker() as session:
        try:
            # Get payment with related data
            result = await session.execute(select(Payment).where(Payment.id == payment_id))
            payment = result.scalar_one_or_none()

            if not payment:
                error_msg = f"Payment {payment_id} not found"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "notifications_sent": [],
                }

            # Only send notifications for completed payments
            if payment.status != PaymentStatus.COMPLETED:
                warning_msg = (
                    f"Skipping notification for payment {payment_id} "
                    f"with status {payment.status.value}"
                )
                logger.warning(warning_msg)
                return {
                    "status": "skipped",
                    "message": warning_msg,
                    "notifications_sent": [],
                }

            # Get tenant details
            result = await session.execute(select(Tenant).where(Tenant.id == payment.tenant_id))
            tenant = result.scalar_one_or_none()

            if not tenant:
                error_msg = f"Tenant {payment.tenant_id} not found"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "notifications_sent": [],
                }

            # Get tenant's user account
            result = await session.execute(select(User).where(User.id == tenant.user_id))
            user = result.scalar_one_or_none()

            if not user:
                error_msg = f"User {tenant.user_id} not found for tenant {tenant.id}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "notifications_sent": [],
                }

            # Prepare notification content
            notification_data = {
                "payment_id": str(payment.id),
                "amount": float(payment.amount),
                "currency": payment.currency,
                "payment_date": payment.payment_date.isoformat(),
                "payment_type": payment.payment_type.value,
                "transaction_reference": payment.transaction_reference or "N/A",
                "tenant_name": user.full_name,
                "tenant_email": user.email,
                "tenant_phone": user.phone,
            }

            # Send email notification
            if user.email:
                try:
                    await _send_email_notification(user.email, notification_data)
                    notifications_sent.append("email")
                    logger.info(f"Email notification sent to {user.email}")
                except Exception as e:
                    error_msg = f"Failed to send email to {user.email}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Send SMS notification (if phone number available)
            if user.phone:
                try:
                    await _send_sms_notification(user.phone, notification_data)
                    notifications_sent.append("sms")
                    logger.info(f"SMS notification sent to {user.phone}")
                except Exception as e:
                    error_msg = f"Failed to send SMS to {user.phone}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Send push notification (if device tokens available)
            # Note: This would require device token storage and FCM/APNS integration
            # Placeholder for future implementation

            return {
                "status": "success" if notifications_sent else "failed",
                "message": (
                    f"Notifications sent via: {', '.join(notifications_sent)}"
                    if notifications_sent
                    else "No notifications sent"
                ),
                "notifications_sent": notifications_sent,
                "errors": errors,
                "payment_id": str(payment_id),
            }

        except Exception as e:
            error_msg = f"Error sending payment confirmation for {payment_id}: {e}"
            logger.exception(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "notifications_sent": notifications_sent,
                "errors": errors + [str(e)],
            }


async def _send_email_notification(email: str, data: dict[str, any]) -> None:
    """Send email notification for payment confirmation.

    Args:
        email: Recipient email address
        data: Payment and tenant data

    Note:
        This is a placeholder implementation. In production, integrate with:
        - SendGrid API
        - AWS SES
        - SMTP server
        - Or other email service
    """
    # TODO: Implement actual email sending
    # For now, just log the email that would be sent

    email_body = f"""
    Dear {data['tenant_name']},

    Your payment has been successfully processed!

    Payment Details:
    - Amount: {data['currency']} {data['amount']}
    - Payment Type: {data['payment_type']}
    - Transaction Reference: {data['transaction_reference']}
    - Payment Date: {data['payment_date']}
    - Payment ID: {data['payment_id']}

    Thank you for your payment. A receipt has been generated and is available in your account.

    If you have any questions, please contact your property manager.

    Best regards,
    Meroghar Property Management
    """

    logger.info(
        f"[EMAIL PLACEHOLDER] Would send email to {email}:\n"
        f"Subject: Payment Confirmation - Rs. {data['amount']}\n"
        f"Body:\n{email_body}"
    )

    # In production, replace above with actual email sending:
    # import smtplib
    # from email.mime.text import MIMEText
    # from email.mime.multipart import MIMEMultipart
    #
    # msg = MIMEMultipart()
    # msg['From'] = "noreply@meroghar.com"
    # msg['To'] = email
    # msg['Subject'] = f"Payment Confirmation - Rs. {data['amount']}"
    # msg.attach(MIMEText(email_body, 'plain'))
    #
    # with smtplib.SMTP('smtp.gmail.com', 587) as server:
    #     server.starttls()
    #     server.login("your_email@gmail.com", "your_password")
    #     server.send_message(msg)


async def _send_sms_notification(phone: str, data: dict[str, any]) -> None:
    """Send SMS notification for payment confirmation.

    Args:
        phone: Recipient phone number
        data: Payment and tenant data

    Note:
        This is a placeholder implementation. In production, integrate with:
        - Twilio SMS API
        - Nepal Telecom SMS Gateway
        - Sparrow SMS (Nepal)
        - Or other SMS service
    """
    # TODO: Implement actual SMS sending
    # For now, just log the SMS that would be sent

    sms_body = (
        f"Meroghar: Payment confirmed! "
        f"Amount: Rs.{data['amount']} "
        f"Type: {data['payment_type']} "
        f"Ref: {data['transaction_reference'][:8]} "
        f"Receipt available in app."
    )

    logger.info(f"[SMS PLACEHOLDER] Would send SMS to {phone}:\n{sms_body}")

    # In production, replace above with actual SMS sending:
    # For Nepal, popular options:
    # 1. Sparrow SMS: https://sparrowsms.com/
    # 2. Nepal Telecom SMS Gateway
    # 3. Twilio (international)
    #
    # Example with Twilio:
    # from twilio.rest import Client
    #
    # client = Client(account_sid, auth_token)
    # message = client.messages.create(
    #     body=sms_body,
    #     from_='+1234567890',
    #     to=phone
    # )


__all__ = ["send_payment_confirmation"]
