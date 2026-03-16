from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import BaseModel


class User(AbstractUser, BaseModel):
    """
    Custom User model extending AbstractUser and our BaseModel (UUID).
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        MANAGER = 'MANAGER', 'Manager'
        STAFF = 'STAFF', 'Staff'
        TENANT = 'TENANT', 'Tenant'
        VENDOR = 'VENDOR', 'Vendor'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)

    def __str__(self):
        return self.username

    def membership_for(self, organization):
        if organization is None:
            return None
        return self.organization_memberships.filter(
            organization=organization,
            is_active=True,
        ).first()

    def has_org_role(self, organization, allowed_roles):
        membership = self.membership_for(organization)
        return bool(membership and membership.role in allowed_roles)
