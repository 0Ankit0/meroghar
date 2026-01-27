from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class InventoryItem(BaseModel):
    class Condition(models.TextChoices):
        NEW = 'NEW', _('New')
        GOOD = 'GOOD', _('Good')
        FAIR = 'FAIR', _('Fair')
        POOR = 'POOR', _('Poor')
        BROKEN = 'BROKEN', _('Broken')

    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='inventory_items'
    )
    unit = models.ForeignKey(
        'housing.Unit',
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Category(models.TextChoices):
        APPLIANCE = 'APPLIANCE', 'Appliance'
        FURNITURE = 'FURNITURE', 'Furniture'
        OTHER = 'OTHER', 'Other'

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )
    
    serial_number = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD
    )
    
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.unit}"
