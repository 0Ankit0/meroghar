from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class WorkOrder(BaseModel):
    class Status(models.TextChoices):
        OPEN = 'OPEN', _('Open')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        RESOLVED = 'RESOLVED', _('Resolved')
        CLOSED = 'CLOSED', _('Closed')
    
    class Priority(models.TextChoices):
        LOW = 'LOW', _('Low')
        MEDIUM = 'MEDIUM', _('Medium')
        HIGH = 'HIGH', _('High')
        EMERGENCY = 'EMERGENCY', _('Emergency')
    
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
        related_name='work_orders'
    )
    unit = models.ForeignKey(
        'housing.Unit',  # Updated to housing app
        on_delete=models.CASCADE,
        related_name='work_orders'
    )
    requester = models.ForeignKey(
        'housing.Tenant',  # Updated to housing app
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_work_orders'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    
    assigned_to = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_work_orders'
    )
    
    # Optional external vendor assignment
    assigned_vendor = models.ForeignKey(
        'operations.Vendor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_work_orders'
    )
    preferred_service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        default=ServiceType.GENERAL,
    )
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    vendor_auto_assigned_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"WO-{self.id.hex[:6].upper()} : {self.title}"
