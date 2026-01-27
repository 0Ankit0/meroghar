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
        from django.core.exceptions import ValidationError
        from django.db.models import Q

        # Date validation
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError(_("End date must be after start date."))

        # Overlap check
        # We need to check if ANY of the assigned units have an overlapping active lease
        # This is strictly for ACTIVE leases or confirmed ones, we might want to exclude CANCELLED/TERMINATED if the logic allows re-leasing
        
        # Note: Since units is ManyToMany, instance needs to be saved to have units. 
        # But clean() is called before save() in ModelForms.
        # If this is a new instance, we might not have access to self.units.all() easily without hacking.
        # However, typically M2M is set after save. 
        # For strict validation usually we do it in a Service layer or Form. 
        # But if we assume 'units' are set (e.g. update) we can check.
        
        # For simplicity in this 'clean' method, we can't easily check M2M on NEW creation before save.
        # A common tailored approach is checking if the user passed 'units' to the form context.
        # OR we rely on the implementation where we might check this in a Service or Serializer.
        
        # BUT, if we want to add the code, here is the logic:
        pass
        # Real implementation would likely need to happen in the text of the application logic 
        # or we accept that M2M validation in model.clean() is tricky for new objects.
        
        # Let's check for specific unit overlap if we can.
        # If we stick to 'one active lease per unit', we should enforce it.
        
        # Strategy: The Application Logic (Service/Serializer) should call this validation 
        # explicitly passing the units to check.
        # But for 'clean' on existing instance:
        
        if self.pk:
            overlapping_leases = Lease.objects.filter(
                organization=self.organization,
                units__in=self.units.all(),
                status=Lease.Status.ACTIVE
            ).exclude(pk=self.pk).filter(
                Q(start_date__lt=self.end_date) & Q(end_date__gt=self.start_date)
            ).distinct()
            
            if overlapping_leases.exists():
                raise ValidationError(_("One or more units have an overlapping active lease."))
