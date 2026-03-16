from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel


class OrganizationMembership(BaseModel):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        ADMIN = 'ADMIN', 'Admin'
        MANAGER = 'MANAGER', 'Manager'
        STAFF = 'STAFF', 'Staff'
        TENANT = 'TENANT', 'Tenant'
        VENDOR = 'VENDOR', 'Vendor'

    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organization_memberships',
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_organization_invites',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user'],
                name='iam_unique_org_user_membership',
            ),
            models.UniqueConstraint(
                fields=['organization'],
                condition=Q(role='OWNER', is_active=True),
                name='iam_unique_active_owner_per_org',
            ),
        ]

    def __str__(self):
        return f"{self.user} @ {self.organization} ({self.role})"
