from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class PropertyInspection(BaseModel):
    class Type(models.TextChoices):
        MOVE_IN = 'MOVE_IN', _('Move In')
        MOVE_OUT = 'MOVE_OUT', _('Move Out')
        ROUTINE = 'ROUTINE', _('Routine')
        COMPLAINT = 'COMPLAINT', _('Complaint Based')

    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='inspections'
    )
    lease = models.ForeignKey(
        'housing.Lease',
        on_delete=models.CASCADE,
        related_name='inspections',
        null=True, blank=True
    )
    unit = models.ForeignKey(
        'housing.Unit',
        on_delete=models.CASCADE,
        related_name='inspections'
    )
    inspector = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_inspections'
    )
    
    inspection_date = models.DateField()
    inspection_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.ROUTINE
    )
    
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Scheduled')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    
    condition_rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Rating 1-5")

    notes = models.TextField(blank=True)
    
    # We can store a summary of damages or condition here
    condition_summary = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.inspection_type} - {self.unit} ({self.inspection_date})"

class InspectionPhoto(BaseModel):
    inspection = models.ForeignKey(
        PropertyInspection,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    image = models.ImageField(upload_to='inspections/')
    caption = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Photo for {self.inspection}"
