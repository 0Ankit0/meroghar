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
        Integrates with SendGrid, SMTP, or other email service based on configuration.
    """
    from ..core.config import get_settings
    
    settings = get_settings()
    
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

    # Check if email backend is configured
    if not (settings.sendgrid_api_key or (settings.smtp_host and settings.smtp_username)):
        logger.warning(
            f"[EMAIL NOT CONFIGURED] Would send email to {email}:\n"
            f"Subject: Payment Confirmation - {data['currency']} {data['amount']}\n"
            f"Please configure SendGrid (SENDGRID_API_KEY) or SMTP settings to enable email sending."
        )
        return

    # Send actual email
    try:
        # Try SendGrid first
        if settings.sendgrid_api_key:
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail

                message = Mail(
                    from_email=(settings.sendgrid_from_email, settings.sendgrid_from_name),
                    to_emails=email,
                    subject=f"Payment Confirmation - {data['currency']} {data['amount']}",
                    plain_text_content=email_body,
                )

                sg = SendGridAPIClient(settings.sendgrid_api_key)
                response = sg.send(message)

                logger.info(
                    f"Payment confirmation email sent via SendGrid to {email}: "
                    f"status={response.status_code}, payment_id={data['payment_id']}"
                )
                return
            except ImportError:
                logger.warning("SendGrid library not installed, falling back to SMTP")
            except Exception as e:
                logger.error(f"SendGrid email failed: {str(e)}, falling back to SMTP")

        # Fall back to SMTP
        if settings.smtp_host and settings.smtp_username and settings.smtp_password:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            msg['To'] = email
            msg['Subject'] = f"Payment Confirmation - {data['currency']} {data['amount']}"
            msg.attach(MIMEText(email_body, 'plain'))

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)

            logger.info(
                f"Payment confirmation email sent via SMTP to {email}: payment_id={data['payment_id']}"
            )
        else:
            logger.warning("SMTP not configured - email not sent")

    except Exception as e:
        logger.error(f"Failed to send payment confirmation email to {email}: {str(e)}", exc_info=True)


async def _send_sms_notification(phone: str, data: dict[str, any]) -> None:
    """Send SMS notification for payment confirmation.

    Args:
        phone: Recipient phone number
        data: Payment and tenant data

    Note:
        Integrates with Twilio SMS, Sparrow SMS (Nepal), or other SMS service.
    """
    from ..core.config import get_settings
    
    settings = get_settings()
    
    sms_body = (
        f"Meroghar: Payment confirmed! "
        f"Amount: {data['currency']}{data['amount']} "
        f"Type: {data['payment_type']} "
        f"Ref: {data['transaction_reference'][:8] if data['transaction_reference'] else 'N/A'} "
        f"Receipt available in app."
    )

    # Check if SMS backend is configured
    if not (settings.twilio_account_sid and settings.twilio_auth_token):
        logger.warning(
            f"[SMS NOT CONFIGURED] Would send SMS to {phone}:\n{sms_body}\n"
            f"Please configure Twilio (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) to enable SMS sending."
        )
        return

    # Send actual SMS via Twilio
    try:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        
        message = client.messages.create(
            body=sms_body,
            from_=settings.twilio_phone_number,
            to=phone
        )

        logger.info(
            f"Payment confirmation SMS sent via Twilio to {phone}: "
            f"sid={message.sid}, payment_id={data['payment_id']}"
        )

    except ImportError:
        logger.error("Twilio library not installed. Install with: pip install twilio")
    except Exception as e:
        logger.error(f"Failed to send payment confirmation SMS to {phone}: {str(e)}", exc_info=True)


__all__ = ["send_payment_confirmation"]
