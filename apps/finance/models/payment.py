from django.db import models, transaction
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Payment(BaseModel):
    class Status(models.TextChoices):
        INITIATED = 'INITIATED', _('Initiated')
        PENDING = 'PENDING', _('Pending')
        SUCCESS = 'SUCCESS', _('Success')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')
    
    class Provider(models.TextChoices):
        KHALTI = 'KHALTI', _('Khalti')
        ESEWA = 'ESEWA', _('eSewa')
        CASH = 'CASH', _('Cash')
        BANK_TRANSFER = 'BANK_TRANSFER', _('Bank Transfer')
    
    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    invoice = models.ForeignKey(
        'finance.Invoice',  # Updated to finance app
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=255, blank=True)
    
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.CASH
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    verified_at = models.DateTimeField(null=True, blank=True)
    provider_payload = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'transaction_id'],
                condition=~models.Q(transaction_id=''),
                name='uniq_payment_provider_transaction_id',
            ),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"

    def apply_reversal(self, reversed_status):
        if reversed_status not in {self.Status.REFUNDED, self.Status.FAILED}:
            raise ValueError("Reversal status must be REFUNDED or FAILED.")

        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('invoice').get(pk=self.pk)

            if payment.status in {self.Status.REFUNDED, self.Status.FAILED}:
                return payment

            invoice = payment.invoice
            if invoice:
                locked_invoice = (
                    invoice.__class__.objects.select_for_update().get(pk=invoice.pk)
                )
                locked_invoice.paid_amount = max(0, locked_invoice.paid_amount - payment.amount)
                if locked_invoice.paid_amount >= locked_invoice.total_amount:
                    locked_invoice.status = locked_invoice.Status.PAID
                elif locked_invoice.paid_amount > 0:
                    locked_invoice.status = locked_invoice.Status.PARTIALLY_PAID
                else:
                    locked_invoice.status = locked_invoice.Status.OVERDUE if locked_invoice.due_date < payment.created_at.date() else locked_invoice.Status.SENT
                locked_invoice.save(update_fields=['paid_amount', 'status', 'updated_at'])

            payment.status = reversed_status
            payment.save(update_fields=['status', 'updated_at'])
            return payment
