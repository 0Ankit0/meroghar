from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from apps.core.models import BaseModel

class User(AbstractUser, BaseModel):
    """
    Custom User model extending AbstractUser and our BaseModel (UUID).
    """
    # AbstractUser already has username, password, email, first_name, last_name, etc.
    # We override id here via BaseModel
    
    # We can add Roles here later or via Group/Permissions
    # For simple RBAC, a role field is often useful.
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        MANAGER = 'MANAGER', 'Manager'
        STAFF = 'STAFF', 'Staff'
        TENANT = 'TENANT', 'Tenant'
        VENDOR = 'VENDOR', 'Vendor'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)
   
    organizations = models.ManyToManyField(
        'iam.Organization',
        related_name='members',
        blank=True
    )
    
    def __str__(self):
        return self.username
