from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Lease(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        ACTIVE = 'ACTIVE', _('Active')
        EXPIRED = 'EXPIRED', _('Expired')
        TERMINATED = 'TERMINATED', _('Terminated')

    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='leases'
    )
    tenant = models.ForeignKey(
        'housing.Tenant',  # Updated to housing app
        on_delete=models.CASCADE,
        related_name='leases'
    )
    units = models.ManyToManyField(
        'housing.Unit',
        related_name='leases'
    )
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    terms_and_conditions = models.TextField(blank=True)
    
    # Store the signed PDF later
    signed_lease_doc = models.FileField(upload_to='leases/', blank=True, null=True)

    def __str__(self):
        return f"Lease: {self.tenant} - {self.units.count()} Units"

    def clean(self):
        # Validate that unit belongs to same org as tenant (optional sanity check)
        pass
