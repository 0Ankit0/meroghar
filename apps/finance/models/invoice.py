from django.db import models
from decimal import Decimal
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Invoice(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        SENT = 'SENT', _('Sent')
        PARTIALLY_PAID = 'PARTIALLY_PAID', _('Partially Paid')
        PAID = 'PAID', _('Paid')
        OVERDUE = 'OVERDUE', _('Overdue')
        CANCELLED = 'CANCELLED', _('Cancelled')

    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    lease = models.ForeignKey(
        'housing.Lease',  # Updated to housing app
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    
    # Amount fields
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    late_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    late_fee_applied_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-invoice_date']

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    @property
    def balance_due(self):
        return self.total_amount + self.late_fee_amount - self.paid_amount

    def apply_late_fee(self, percentage=Decimal('0.05')):
        if self.status in [self.Status.PAID, self.Status.CANCELLED]:
            return False
        if self.due_date >= timezone.now().date():
            return False
        if self.balance_due <= 0:
            return False
        if self.late_fee_amount > 0:
            return False

        self.late_fee_amount = (self.total_amount * percentage).quantize(Decimal('0.01'))
        self.late_fee_applied_at = timezone.now()
        self.status = self.Status.OVERDUE
        self.save(update_fields=['late_fee_amount', 'late_fee_applied_at', 'status', 'updated_at'])
        return True
