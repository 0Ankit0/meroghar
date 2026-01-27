from django.db import models
from apps.core.models import BaseModel

class Tenant(BaseModel):
    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='tenants'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # ID/Documents
    id_proof_number = models.CharField(max_length=100, blank=True)
    
    # Link to System User (for Mobile App access)
    user = models.OneToOneField(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_profile'
    )
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return self.full_name
