from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Expense(BaseModel):
    class Category(models.TextChoices):
        MAINTENANCE = 'MAINTENANCE', _('Maintenance')
        UTILITIES = 'UTILITIES', _('Utilities')
        TAX = 'TAX', _('Tax')
        INSURANCE = 'INSURANCE', _('Insurance')
        MANAGEMENT = 'MANAGEMENT', _('Management Fee')
        OTHER = 'OTHER', _('Other')

    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    property = models.ForeignKey(
        'housing.Property',
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    unit = models.ForeignKey(
        'housing.Unit',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expenses'
    )
    
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.MAINTENANCE
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    description = models.TextField(blank=True)
    
    receipt = models.FileField(upload_to='expenses/', blank=True, null=True)
    
    # Link to a work order if applicable
    work_order = models.ForeignKey(
        'operations.WorkOrder',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expenses'
    )

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.expense_date})"
