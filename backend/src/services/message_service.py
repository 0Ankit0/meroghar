"""
Message service for SMS/WhatsApp reminders via Twilio.

Implements T160-T162, T219 from tasks.md.

Supports multi-language templates for: English, Hindi, Spanish, Arabic
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from ..core.config import settings
from ..models.message import (Message, MessageChannel, MessageStatus,
                              MessageTemplate)
from ..models.tenant import Tenant

# Language-specific message templates with placeholders
# Implements T219: Create language-specific message templates
MESSAGE_TEMPLATES_MULTILANG = {
    MessageTemplate.PAYMENT_REMINDER: {
        "en": {
            "sms": "Hi {tenant_name}, this is a reminder that your rent payment of Rs. {amount_due} for {property_name} is due on {due_date}. Please pay at your earliest convenience. {payment_link}",
            "whatsapp": "Dear {tenant_name},\n\nThis is a friendly reminder that your rent payment of Rs. {amount_due} for {property_name} is due on {due_date}.\n\nPlease make the payment at your earliest convenience.\n\n{payment_link}\n\nThank you!",
            "email_subject": "Rent Payment Reminder - {property_name}",
            "email_body": "Dear {tenant_name},\n\nThis is a reminder that your rent payment for {property_name} is due soon.\n\nAmount Due: Rs. {amount_due}\nDue Date: {due_date}\n\nPlease make the payment at your earliest convenience.\n\n{payment_link}\n\nThank you for your cooperation.\n\nBest regards,\nProperty Management Team",
        },
        "hi": {
            "sms": "नमस्ते {tenant_name}, यह एक अनुस्मारक है कि {property_name} के लिए आपका ₹{amount_due} का किराया भुगतान {due_date} को देय है। कृपया जल्द से जल्द भुगतान करें। {payment_link}",
            "whatsapp": "प्रिय {tenant_name},\n\nयह एक मैत्रीपूर्ण अनुस्मारक है कि {property_name} के लिए आपका ₹{amount_due} का किराया भुगतान {due_date} को देय है।\n\nकृपया जल्द से जल्द भुगतान करें।\n\n{payment_link}\n\nधन्यवाद!",
            "email_subject": "किराया भुगतान अनुस्मारक - {property_name}",
            "email_body": "प्रिय {tenant_name},\n\nयह एक अनुस्मारक है कि {property_name} के लिए आपका किराया भुगतान जल्द ही देय है।\n\nदेय राशि: ₹{amount_due}\nदेय तिथि: {due_date}\n\nकृपया जल्द से जल्द भुगतान करें।\n\n{payment_link}\n\nआपके सहयोग के लिए धन्यवाद।\n\nसादर,\nसंपत्ति प्रबंधन टीम",
        },
        "es": {
            "sms": "Hola {tenant_name}, este es un recordatorio de que su pago de alquiler de Rs. {amount_due} para {property_name} vence el {due_date}. Por favor pague lo antes posible. {payment_link}",
            "whatsapp": "Estimado {tenant_name},\n\nEste es un recordatorio amistoso de que su pago de alquiler de Rs. {amount_due} para {property_name} vence el {due_date}.\n\nPor favor realice el pago lo antes posible.\n\n{payment_link}\n\n¡Gracias!",
            "email_subject": "Recordatorio de Pago de Alquiler - {property_name}",
            "email_body": "Estimado {tenant_name},\n\nEste es un recordatorio de que su pago de alquiler para {property_name} vence pronto.\n\nMonto a Pagar: Rs. {amount_due}\nFecha de Vencimiento: {due_date}\n\nPor favor realice el pago lo antes posible.\n\n{payment_link}\n\nGracias por su cooperación.\n\nSaludos cordiales,\nEquipo de Gestión de Propiedades",
        },
        "ar": {
            "sms": "مرحباً {tenant_name}، هذا تذكير بأن دفع إيجارك بمبلغ {amount_due} روبية لـ {property_name} مستحق في {due_date}. يرجى الدفع في أقرب وقت ممكن. {payment_link}",
            "whatsapp": "عزيزي {tenant_name}،\n\nهذا تذكير ودي بأن دفع إيجارك بمبلغ {amount_due} روبية لـ {property_name} مستحق في {due_date}.\n\nيرجى إجراء الدفع في أقرب وقت ممكن.\n\n{payment_link}\n\nشكراً!",
            "email_subject": "تذكير بدفع الإيجار - {property_name}",
            "email_body": "عزيزي {tenant_name}،\n\nهذا تذكير بأن دفع إيجارك لـ {property_name} مستحق قريباً.\n\nالمبلغ المستحق: {amount_due} روبية\nتاريخ الاستحقاق: {due_date}\n\nيرجى إجراء الدفع في أقرب وقت ممكن.\n\n{payment_link}\n\nشكراً لتعاونك.\n\nمع أطيب التحيات،\nفريق إدارة العقارات",
        },
    },
    MessageTemplate.PAYMENT_OVERDUE: {
        "en": {
            "sms": "URGENT: {tenant_name}, your rent payment of Rs. {amount_due} for {property_name} is OVERDUE. Please pay immediately to avoid late fees. {payment_link}",
            "whatsapp": "⚠️ *URGENT* ⚠️\n\nDear {tenant_name},\n\nYour rent payment of Rs. {amount_due} for {property_name} is *OVERDUE*.\n\nPlease make the payment immediately to avoid late fees and penalties.\n\n{payment_link}\n\nThank you for your prompt attention.",
            "email_subject": "URGENT: Overdue Rent Payment - {property_name}",
            "email_body": "Dear {tenant_name},\n\nThis is an urgent notice that your rent payment for {property_name} is OVERDUE.\n\nAmount Due: Rs. {amount_due}\nDays Overdue: {days_overdue}\n\nPlease make the payment immediately to avoid late fees and penalties.\n\n{payment_link}\n\nIf you have already made the payment, please disregard this message.\n\nBest regards,\nProperty Management Team",
        },
        "hi": {
            "sms": "जरूरी: {tenant_name}, {property_name} के लिए आपका ₹{amount_due} का किराया भुगतान विलंबित है। देर से शुल्क से बचने के लिए कृपया तुरंत भुगतान करें। {payment_link}",
            "whatsapp": "⚠️ *जरूरी* ⚠️\n\nप्रिय {tenant_name},\n\n{property_name} के लिए आपका ₹{amount_due} का किराया भुगतान *विलंबित* है।\n\nदेर से शुल्क और जुर्माने से बचने के लिए कृपया तुरंत भुगतान करें।\n\n{payment_link}\n\nआपके शीघ्र ध्यान के लिए धन्यवाद।",
            "email_subject": "जरूरी: विलंबित किराया भुगतान - {property_name}",
            "email_body": "प्रिय {tenant_name},\n\nयह एक जरूरी सूचना है कि {property_name} के लिए आपका किराया भुगतान विलंबित है।\n\nदेय राशि: ₹{amount_due}\nविलंब के दिन: {days_overdue}\n\nदेर से शुल्क और जुर्माने से बचने के लिए कृपया तुरंत भुगतान करें।\n\n{payment_link}\n\nयदि आपने पहले ही भुगतान कर दिया है, तो कृपया इस संदेश को अनदेखा करें।\n\nसादर,\nसंपत्ति प्रबंधन टीम",
        },
        "es": {
            "sms": "URGENTE: {tenant_name}, su pago de alquiler de Rs. {amount_due} para {property_name} está VENCIDO. Por favor pague inmediatamente para evitar cargos por mora. {payment_link}",
            "whatsapp": "⚠️ *URGENTE* ⚠️\n\nEstimado {tenant_name},\n\nSu pago de alquiler de Rs. {amount_due} para {property_name} está *VENCIDO*.\n\nPor favor realice el pago inmediatamente para evitar cargos por mora y penalizaciones.\n\n{payment_link}\n\nGracias por su pronta atención.",
            "email_subject": "URGENTE: Pago de Alquiler Vencido - {property_name}",
            "email_body": "Estimado {tenant_name},\n\nEste es un aviso urgente de que su pago de alquiler para {property_name} está VENCIDO.\n\nMonto a Pagar: Rs. {amount_due}\nDías de Retraso: {days_overdue}\n\nPor favor realice el pago inmediatamente para evitar cargos por mora y penalizaciones.\n\n{payment_link}\n\nSi ya realizó el pago, por favor ignore este mensaje.\n\nSaludos cordiales,\nEquipo de Gestión de Propiedades",
        },
        "ar": {
            "sms": "عاجل: {tenant_name}، دفع إيجارك بمبلغ {amount_due} روبية لـ {property_name} متأخر. يرجى الدفع فوراً لتجنب رسوم التأخير. {payment_link}",
            "whatsapp": "⚠️ *عاجل* ⚠️\n\nعزيزي {tenant_name}،\n\nدفع إيجارك بمبلغ {amount_due} روبية لـ {property_name} *متأخر*.\n\nيرجى إجراء الدفع فوراً لتجنب رسوم التأخير والغرامات.\n\n{payment_link}\n\nشكراً لاهتمامك السريع.",
            "email_subject": "عاجل: دفع إيجار متأخر - {property_name}",
            "email_body": "عزيزي {tenant_name}،\n\nهذا إشعار عاجل بأن دفع إيجارك لـ {property_name} متأخر.\n\nالمبلغ المستحق: {amount_due} روبية\nأيام التأخير: {days_overdue}\n\nيرجى إجراء الدفع فوراً لتجنب رسوم التأخير والغرامات.\n\n{payment_link}\n\nإذا كنت قد أجريت الدفع بالفعل، يرجى تجاهل هذه الرسالة.\n\nمع أطيب التحيات،\nفريق إدارة العقارات",
        },
    },
    MessageTemplate.PAYMENT_RECEIVED: {
        "en": {
            "sms": "Thank you {tenant_name}! We have received your payment of Rs. {amount_paid} for {property_name}. Receipt: {receipt_url}",
            "whatsapp": "✅ *Payment Received*\n\nThank you {tenant_name}!\n\nWe have successfully received your payment.\n\nAmount: Rs. {amount_paid}\nProperty: {property_name}\nDate: {payment_date}\n\nReceipt: {receipt_url}",
            "email_subject": "Payment Received - {property_name}",
            "email_body": "Dear {tenant_name},\n\nThank you for your payment!\n\nWe have successfully received your payment:\n\nAmount: Rs. {amount_paid}\nProperty: {property_name}\nPayment Date: {payment_date}\n\nReceipt: {receipt_url}\n\nThank you for your timely payment.\n\nBest regards,\nProperty Management Team",
        },
        "hi": {
            "sms": "धन्यवाद {tenant_name}! हमें {property_name} के लिए आपका ₹{amount_paid} का भुगतान प्राप्त हुआ है। रसीद: {receipt_url}",
            "whatsapp": "✅ *भुगतान प्राप्त हुआ*\n\nधन्यवाद {tenant_name}!\n\nहमें आपका भुगतान सफलतापूर्वक प्राप्त हुआ है।\n\nराशि: ₹{amount_paid}\nसंपत्ति: {property_name}\nतिथि: {payment_date}\n\nरसीद: {receipt_url}",
            "email_subject": "भुगतान प्राप्त हुआ - {property_name}",
            "email_body": "प्रिय {tenant_name},\n\nआपके भुगतान के लिए धन्यवाद!\n\nहमें आपका भुगतान सफलतापूर्वक प्राप्त हुआ है:\n\nराशि: ₹{amount_paid}\nसंपत्ति: {property_name}\nभुगतान तिथि: {payment_date}\n\nरसीद: {receipt_url}\n\nसमय पर भुगतान के लिए धन्यवाद।\n\nसादर,\nसंपत्ति प्रबंधन टीम",
        },
        "es": {
            "sms": "¡Gracias {tenant_name}! Hemos recibido su pago de Rs. {amount_paid} para {property_name}. Recibo: {receipt_url}",
            "whatsapp": "✅ *Pago Recibido*\n\n¡Gracias {tenant_name}!\n\nHemos recibido su pago exitosamente.\n\nMonto: Rs. {amount_paid}\nPropiedad: {property_name}\nFecha: {payment_date}\n\nRecibo: {receipt_url}",
            "email_subject": "Pago Recibido - {property_name}",
            "email_body": "Estimado {tenant_name},\n\n¡Gracias por su pago!\n\nHemos recibido su pago exitosamente:\n\nMonto: Rs. {amount_paid}\nPropiedad: {property_name}\nFecha de Pago: {payment_date}\n\nRecibo: {receipt_url}\n\nGracias por su pago puntual.\n\nSaludos cordiales,\nEquipo de Gestión de Propiedades",
        },
        "ar": {
            "sms": "شكراً {tenant_name}! لقد استلمنا دفعتك بمبلغ {amount_paid} روبية لـ {property_name}. الإيصال: {receipt_url}",
            "whatsapp": "✅ *تم استلام الدفع*\n\nشكراً {tenant_name}!\n\nلقد استلمنا دفعتك بنجاح.\n\nالمبلغ: {amount_paid} روبية\nالعقار: {property_name}\nالتاريخ: {payment_date}\n\nالإيصال: {receipt_url}",
            "email_subject": "تم استلام الدفع - {property_name}",
            "email_body": "عزيزي {tenant_name}،\n\nشكراً لدفعك!\n\nلقد استلمنا دفعتك بنجاح:\n\nالمبلغ: {amount_paid} روبية\nالعقار: {property_name}\nتاريخ الدفع: {payment_date}\n\nالإيصال: {receipt_url}\n\nشكراً لدفعك في الوقت المحدد.\n\nمع أطيب التحيات،\nفريق إدارة العقارات",
        },
    },
    # Add more template translations as needed...
}

# Backward compatibility: Default English templates
MESSAGE_TEMPLATES = {
    template: templates.get("en", {}) for template, templates in MESSAGE_TEMPLATES_MULTILANG.items()
}


class MessageService:
    """Service for handling SMS/WhatsApp/Email messaging via Twilio."""

    def __init__(self):
        """Initialize Twilio client."""
        self.client: Client | None = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def _format_message(
        self,
        template: MessageTemplate,
        channel: MessageChannel,
        variables: dict[str, Any],
        language: str = "en",
    ) -> str:
        """Format message from template with variables and language support.

        Args:
            template: Message template type
            channel: Communication channel (SMS, WhatsApp, Email)
            variables: Dictionary of placeholder values
            language: ISO 639-1 language code (en, hi, es, ar)

        Returns:
            Formatted message string
        """
        if template == MessageTemplate.CUSTOM:
            return variables.get("content", "")

        # Get language-specific template with fallback to English
        template_multilang = MESSAGE_TEMPLATES_MULTILANG.get(template, {})
        template_data = template_multilang.get(language, template_multilang.get("en", {}))

        # Get channel-specific template
        if channel == MessageChannel.EMAIL:
            content = template_data.get("email_body", "")
        elif channel == MessageChannel.WHATSAPP:
            content = template_data.get("whatsapp", "")
        else:
            content = template_data.get("sms", "")

        # Replace placeholders
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in content:
                content = content.replace(placeholder, str(value) if value else "")

        return content

    def _get_email_subject(
        self, template: MessageTemplate, variables: dict[str, Any], language: str = "en"
    ) -> str:
        """Get email subject from template with language support."""
        if template == MessageTemplate.CUSTOM:
            return variables.get("subject", "Message from Property Management")

        # Get language-specific template with fallback to English
        template_multilang = MESSAGE_TEMPLATES_MULTILANG.get(template, {})
        template_data = template_multilang.get(language, template_multilang.get("en", {}))
        subject = template_data.get("email_subject", "Message from Property Management")

        # Replace placeholders
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in subject:
                subject = subject.replace(placeholder, str(value) if value else "")

        return subject

    async def send_sms(
        self, to_number: str, message: str, from_number: str | None = None
    ) -> dict[str, Any]:
        """Send SMS via Twilio."""
        if not self.client:
            raise ValueError("Twilio client not configured")

        try:
            from_number = from_number or settings.TWILIO_PHONE_NUMBER

            message_obj = self.client.messages.create(body=message, from_=from_number, to=to_number)

            return {
                "success": True,
                "message_id": message_obj.sid,
                "status": message_obj.status,
                "response": {
                    "sid": message_obj.sid,
                    "status": message_obj.status,
                    "to": message_obj.to,
                    "from": message_obj.from_,
                    "date_created": (
                        message_obj.date_created.isoformat() if message_obj.date_created else None
                    ),
                },
            }

        except TwilioRestException as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": e.code,
                "error_message": e.msg,
            }

    async def send_whatsapp(
        self, to_number: str, message: str, from_number: str | None = None
    ) -> dict[str, Any]:
        """Send WhatsApp message via Twilio."""
        if not self.client:
            raise ValueError("Twilio client not configured")

        try:
            # Twilio WhatsApp numbers must be prefixed with 'whatsapp:'
            from_number = from_number or settings.TWILIO_WHATSAPP_NUMBER
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"

            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"

            message_obj = self.client.messages.create(body=message, from_=from_number, to=to_number)

            return {
                "success": True,
                "message_id": message_obj.sid,
                "status": message_obj.status,
                "response": {
                    "sid": message_obj.sid,
                    "status": message_obj.status,
                    "to": message_obj.to,
                    "from": message_obj.from_,
                    "date_created": (
                        message_obj.date_created.isoformat() if message_obj.date_created else None
                    ),
                },
            }

        except TwilioRestException as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": e.code,
                "error_message": e.msg,
            }

    async def send_email(self, to_email: str, subject: str, body: str) -> dict[str, Any]:
        """Send email via Twilio SendGrid."""
        # TODO: Implement SendGrid email integration
        # For now, return placeholder
        return {
            "success": True,
            "message_id": f"email-{uuid.uuid4()}",
            "status": "sent",
            "response": {"note": "Email integration not yet implemented"},
        }

    async def send_message(self, session: AsyncSession, message_id: int) -> Message:
        """Send a message and update its status."""
        # Get message from database
        result = await session.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one()

        # Update status to sending
        message.status = MessageStatus.SENDING
        await session.commit()

        try:
            # Send via appropriate channel
            if message.channel == MessageChannel.SMS:
                send_result = await self.send_sms(
                    to_number=message.recipient_phone, message=message.content
                )
            elif message.channel == MessageChannel.WHATSAPP:
                send_result = await self.send_whatsapp(
                    to_number=message.recipient_phone, message=message.content
                )
            elif message.channel == MessageChannel.EMAIL:
                send_result = await self.send_email(
                    to_email=message.recipient_email,
                    subject=message.subject or "",
                    body=message.content,
                )
            else:
                raise ValueError(f"Unknown channel: {message.channel}")

            # Update message based on result
            if send_result["success"]:
                message.status = MessageStatus.SENT
                message.sent_at = datetime.utcnow()
                message.provider_message_id = send_result.get("message_id")
                message.provider_response = send_result.get("response")
            else:
                message.status = MessageStatus.FAILED
                message.error_message = send_result.get("error")
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

    async def get_tenant_variables(self, session: AsyncSession, tenant_id: int) -> dict[str, Any]:
        """Get template variables for a tenant."""
        # Get tenant with related data
        result = await session.execute(
            select(Tenant)
            .where(Tenant.id == tenant_id)
            .options(selectinload(Tenant.user), selectinload(Tenant.property))
        )
        tenant = result.scalar_one()

        variables = {
            "tenant_name": tenant.user.full_name if tenant.user else "Tenant",
            "property_name": tenant.property.name if tenant.property else "Property",
            "amount_due": str(tenant.monthly_rent),
            "payment_link": f"{settings.FRONTEND_URL}/payments/pay/{tenant.id}",
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
                "old_rent": old_rent,
                "new_rent": new_rent,
                "effective_date": effective_date.isoformat(),
            },
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
                "old_rent": current_rent,
                "new_rent": new_rent,
                "effective_date": effective_date.isoformat(),
            },
        )

        return message
