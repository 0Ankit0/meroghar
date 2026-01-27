from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Vendor(BaseModel):
    class ServiceType(models.TextChoices):
        PLUMBING = 'PLUMBING', _('Plumbing')
        ELECTRICAL = 'ELECTRICAL', _('Electrical')
        HVAC = 'HVAC', _('HVAC')
        GENERAL = 'GENERAL', _('General Maintenance')
        CLEANING = 'CLEANING', _('Cleaning')
        LANDSCAPING = 'LANDSCAPING', _('Landscaping')
        OTHER = 'OTHER', _('Other')

    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='vendors'
    )
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        default=ServiceType.GENERAL
    )
    
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    address = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.company_name
