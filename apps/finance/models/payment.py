from django.db import models
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

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"
