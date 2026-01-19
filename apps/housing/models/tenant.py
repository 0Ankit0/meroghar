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
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return self.full_name
