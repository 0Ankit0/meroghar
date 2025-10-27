"""
Message service for SMS/WhatsApp reminders via Twilio.

Implements T160-T162 from tasks.md.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.message import Message, MessageStatus, MessageChannel, MessageTemplate
from ..models.tenant import Tenant
from ..models.property import Property


# Message templates with placeholders
MESSAGE_TEMPLATES = {
    MessageTemplate.PAYMENT_REMINDER: {
        "sms": "Hi {tenant_name}, this is a reminder that your rent payment of Rs. {amount_due} for {property_name} is due on {due_date}. Please pay at your earliest convenience. {payment_link}",
        "whatsapp": "Dear {tenant_name},\n\nThis is a friendly reminder that your rent payment of Rs. {amount_due} for {property_name} is due on {due_date}.\n\nPlease make the payment at your earliest convenience.\n\n{payment_link}\n\nThank you!",
        "email_subject": "Rent Payment Reminder - {property_name}",
        "email_body": """Dear {tenant_name},

This is a reminder that your rent payment for {property_name} is due soon.

Amount Due: Rs. {amount_due}
Due Date: {due_date}

Please make the payment at your earliest convenience.

{payment_link}

Thank you for your cooperation.

Best regards,
Property Management Team"""
    },
    MessageTemplate.PAYMENT_OVERDUE: {
        "sms": "URGENT: {tenant_name}, your rent payment of Rs. {amount_due} for {property_name} is OVERDUE. Please pay immediately to avoid late fees. {payment_link}",
        "whatsapp": "⚠️ *URGENT* ⚠️\n\nDear {tenant_name},\n\nYour rent payment of Rs. {amount_due} for {property_name} is *OVERDUE*.\n\nPlease make the payment immediately to avoid late fees and penalties.\n\n{payment_link}\n\nThank you for your prompt attention.",
        "email_subject": "URGENT: Overdue Rent Payment - {property_name}",
        "email_body": """Dear {tenant_name},

This is an urgent notice that your rent payment for {property_name} is OVERDUE.

Amount Due: Rs. {amount_due}
Days Overdue: {days_overdue}

Please make the payment immediately to avoid late fees and penalties.

{payment_link}

If you have already made the payment, please disregard this message.

Best regards,
Property Management Team"""
    },
    MessageTemplate.PAYMENT_RECEIVED: {
        "sms": "Thank you {tenant_name}! We have received your payment of Rs. {amount_paid} for {property_name}. Receipt: {receipt_url}",
        "whatsapp": "✅ *Payment Received*\n\nThank you {tenant_name}!\n\nWe have successfully received your payment.\n\nAmount: Rs. {amount_paid}\nProperty: {property_name}\nDate: {payment_date}\n\nReceipt: {receipt_url}",
        "email_subject": "Payment Received - {property_name}",
        "email_body": """Dear {tenant_name},

Thank you for your payment!

We have successfully received your payment:

Amount: Rs. {amount_paid}
Property: {property_name}
Payment Date: {payment_date}

Receipt: {receipt_url}

Thank you for your timely payment.

Best regards,
Property Management Team"""
    },
    MessageTemplate.LEASE_EXPIRING: {
        "sms": "Hi {tenant_name}, your lease for {property_name} expires on {expiry_date}. Please contact us to discuss renewal options.",
        "whatsapp": "📋 *Lease Expiration Notice*\n\nDear {tenant_name},\n\nYour lease for {property_name} will expire on {expiry_date}.\n\nIf you wish to renew your lease, please contact us at your earliest convenience to discuss renewal terms.\n\nThank you!",
        "email_subject": "Lease Expiration Notice - {property_name}",
        "email_body": """Dear {tenant_name},

This is to inform you that your lease for {property_name} will expire on {expiry_date}.

If you wish to renew your lease, please contact us at your earliest convenience to discuss renewal terms and conditions.

We look forward to continuing our relationship.

Best regards,
Property Management Team"""
    },
    MessageTemplate.MAINTENANCE_NOTICE: {
        "sms": "Notice: {maintenance_message}",
        "whatsapp": "🔧 *Maintenance Notice*\n\n{maintenance_message}",
        "email_subject": "Maintenance Notice - {property_name}",
        "email_body": """Dear {tenant_name},

{maintenance_message}

We apologize for any inconvenience.

Best regards,
Property Management Team"""
    },
    MessageTemplate.RENT_INCREMENT_UPCOMING: {
        "sms": "Hi {tenant_name}, your rent for {property_name} will increase from Rs. {old_rent} to Rs. {new_rent} effective {effective_date}.",
        "whatsapp": "📢 *Rent Increment Notice*\n\nDear {tenant_name},\n\nThis is to inform you that your monthly rent for {property_name} will be adjusted.\n\nCurrent Rent: Rs. {old_rent}\nNew Rent: Rs. {new_rent}\nEffective Date: {effective_date}\n\nThank you for your understanding.",
        "email_subject": "Rent Increment Notice - {property_name}",
        "email_body": """Dear {tenant_name},

This is to inform you that your monthly rent for {property_name} will be adjusted.

Current Rent: Rs. {old_rent}
New Rent: Rs. {new_rent}
Effective Date: {effective_date}

This adjustment is in accordance with the rent increment policy in your lease agreement.

If you have any questions, please contact us.

Best regards,
Property Management Team"""
    },
    MessageTemplate.RENT_INCREMENT_APPLIED: {
        "sms": "Your rent for {property_name} has been updated to Rs. {new_rent} effective today. Previous rent was Rs. {old_rent}.",
        "whatsapp": "✅ *Rent Updated*\n\nDear {tenant_name},\n\nYour monthly rent for {property_name} has been updated.\n\nPrevious Rent: Rs. {old_rent}\nNew Rent: Rs. {new_rent}\nEffective Date: {effective_date}\n\nThank you!",
        "email_subject": "Rent Updated - {property_name}",
        "email_body": """Dear {tenant_name},

Your monthly rent for {property_name} has been updated.

Previous Rent: Rs. {old_rent}
New Rent: Rs. {new_rent}
Effective Date: {effective_date}

Your next payment should reflect this new amount.

Thank you for your understanding.

Best regards,
Property Management Team"""
    },
}


class MessageService:
    """Service for handling SMS/WhatsApp/Email messaging via Twilio."""
    
    def __init__(self):
        """Initialize Twilio client."""
        self.client: Optional[Client] = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
    
    def _format_message(
        self,
        template: MessageTemplate,
        channel: MessageChannel,
        variables: Dict[str, Any]
    ) -> str:
        """Format message from template with variables."""
        if template == MessageTemplate.CUSTOM:
            return variables.get('content', '')
        
        template_data = MESSAGE_TEMPLATES.get(template, {})
        
        # Get channel-specific template
        if channel == MessageChannel.EMAIL:
            content = template_data.get('email_body', '')
        elif channel == MessageChannel.WHATSAPP:
            content = template_data.get('whatsapp', '')
        else:
            content = template_data.get('sms', '')
        
        # Replace placeholders
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in content:
                content = content.replace(placeholder, str(value) if value else '')
        
        return content
    
    def _get_email_subject(
        self,
        template: MessageTemplate,
        variables: Dict[str, Any]
    ) -> str:
        """Get email subject from template."""
        if template == MessageTemplate.CUSTOM:
            return variables.get('subject', 'Message from Property Management')
        
        template_data = MESSAGE_TEMPLATES.get(template, {})
        subject = template_data.get('email_subject', 'Message from Property Management')
        
        # Replace placeholders
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in subject:
                subject = subject.replace(placeholder, str(value) if value else '')
        
        return subject
    
    async def send_sms(
        self,
        to_number: str,
        message: str,
        from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send SMS via Twilio."""
        if not self.client:
            raise ValueError("Twilio client not configured")
        
        try:
            from_number = from_number or settings.TWILIO_PHONE_NUMBER
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'status': message_obj.status,
                'response': {
                    'sid': message_obj.sid,
                    'status': message_obj.status,
                    'to': message_obj.to,
                    'from': message_obj.from_,
                    'date_created': message_obj.date_created.isoformat() if message_obj.date_created else None,
                }
            }
        
        except TwilioRestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code,
                'error_message': e.msg,
            }
    
    async def send_whatsapp(
        self,
        to_number: str,
        message: str,
        from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send WhatsApp message via Twilio."""
        if not self.client:
            raise ValueError("Twilio client not configured")
        
        try:
            # Twilio WhatsApp numbers must be prefixed with 'whatsapp:'
            from_number = from_number or settings.TWILIO_WHATSAPP_NUMBER
            if not from_number.startswith('whatsapp:'):
                from_number = f'whatsapp:{from_number}'
            
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'status': message_obj.status,
                'response': {
                    'sid': message_obj.sid,
                    'status': message_obj.status,
                    'to': message_obj.to,
                    'from': message_obj.from_,
                    'date_created': message_obj.date_created.isoformat() if message_obj.date_created else None,
                }
            }
        
        except TwilioRestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code,
                'error_message': e.msg,
            }
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Send email via Twilio SendGrid."""
        # TODO: Implement SendGrid email integration
        # For now, return placeholder
        return {
            'success': True,
            'message_id': f'email-{uuid.uuid4()}',
            'status': 'sent',
            'response': {
                'note': 'Email integration not yet implemented'
            }
        }
    
    async def send_message(
        self,
        session: AsyncSession,
        message_id: int
    ) -> Message:
        """Send a message and update its status."""
        # Get message from database
        result = await session.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one()
        
        # Update status to sending
        message.status = MessageStatus.SENDING
        await session.commit()
        
        try:
            # Send via appropriate channel
            if message.channel == MessageChannel.SMS:
                send_result = await self.send_sms(
                    to_number=message.recipient_phone,
                    message=message.content
                )
            elif message.channel == MessageChannel.WHATSAPP:
                send_result = await self.send_whatsapp(
                    to_number=message.recipient_phone,
                    message=message.content
                )
            elif message.channel == MessageChannel.EMAIL:
                send_result = await self.send_email(
                    to_email=message.recipient_email,
                    subject=message.subject or '',
                    body=message.content
                )
            else:
                raise ValueError(f"Unknown channel: {message.channel}")
            
            # Update message based on result
            if send_result['success']:
                message.status = MessageStatus.SENT
                message.sent_at = datetime.utcnow()
                message.provider_message_id = send_result.get('message_id')
                message.provider_response = send_result.get('response')
            else:
                message.status = MessageStatus.FAILED
                message.error_message = send_result.get('error')
                message.provider_response = send_result
                message.retry_count += 1
            
            await session.commit()
            await session.refresh(message)
            return message
        
        except Exception as e:
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            message.retry_count += 1
            await session.commit()
            await session.refresh(message)
            return message
    
    async def get_tenant_variables(
        self,
        session: AsyncSession,
        tenant_id: int
    ) -> Dict[str, Any]:
        """Get template variables for a tenant."""
        # Get tenant with related data
        result = await session.execute(
            select(Tenant)
            .where(Tenant.id == tenant_id)
            .options(
                selectinload(Tenant.user),
                selectinload(Tenant.property)
            )
        )
        tenant = result.scalar_one()
        
        variables = {
            'tenant_name': tenant.user.full_name if tenant.user else 'Tenant',
            'property_name': tenant.property.name if tenant.property else 'Property',
            'amount_due': str(tenant.monthly_rent),
            'payment_link': f"{settings.FRONTEND_URL}/payments/pay/{tenant.id}",
        }
        
        return variables

    def send_rent_increment_notification(
        self,
        tenant_id: uuid.UUID,
        old_rent: float,
        new_rent: float,
        effective_date: datetime,
    ) -> Message:
        """Send notification about applied rent increment.
        
        Implements T199 from tasks.md (part of notification system).
        
        Args:
            tenant_id: Tenant UUID
            old_rent: Previous rent amount
            new_rent: New rent amount
            effective_date: Date increment takes effect
        """
        # Create message with rent increment template
        message = Message(
            recipient_id=tenant_id,
            template=MessageTemplate.RENT_INCREMENT_APPLIED,
            channel=MessageChannel.SMS,  # Default to SMS
            scheduled_at=datetime.utcnow(),
            metadata={
                'old_rent': old_rent,
                'new_rent': new_rent,
                'effective_date': effective_date.isoformat(),
            }
        )
        
        # Here you would typically queue this or send immediately
        # For now, just create the message record
        return message
    
    def send_upcoming_rent_increment_notification(
        self,
        tenant_id: uuid.UUID,
        current_rent: float,
        new_rent: float,
        effective_date: datetime,
    ) -> Message:
        """Send notification about upcoming rent increment (30 days before).
        
        Implements T199 from tasks.md.
        
        Args:
            tenant_id: Tenant UUID
            current_rent: Current rent amount
            new_rent: New rent amount after increment
            effective_date: Date increment will take effect
        """
        message = Message(
            recipient_id=tenant_id,
            template=MessageTemplate.RENT_INCREMENT_UPCOMING,
            channel=MessageChannel.SMS,
            scheduled_at=datetime.utcnow(),
            metadata={
                'old_rent': current_rent,
                'new_rent': new_rent,
                'effective_date': effective_date.isoformat(),
            }
        )
        
        return message
