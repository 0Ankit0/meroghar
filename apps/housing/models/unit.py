from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Unit(BaseModel):
    class Status(models.TextChoices):
        VACANT = 'VACANT', _('Vacant')
        OCCUPIED = 'OCCUPIED', _('Occupied')
        MAINTENANCE = 'MAINTENANCE', _('Under Maintenance')

    property = models.ForeignKey(
        'housing.Property',  # Updated to housing app
        on_delete=models.CASCADE,
        related_name='units'
    )
    unit_number = models.CharField(max_length=50)
    floor = models.CharField(max_length=50, blank=True)
    bedrooms = models.PositiveSmallIntegerField(default=1)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    
    area_sqft = models.PositiveIntegerField(null=True, blank=True)
    
    # Financials
    market_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.VACANT
    )

    class Meta:
        unique_together = ('property', 'unit_number')

    def __str__(self):
        return f"{self.property.name} - Unit {self.unit_number}"
