from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import BaseModel


class User(AbstractUser, BaseModel):
    """
    Custom User model extending AbstractUser and our BaseModel (UUID).
    """

    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        MEMBER = 'MEMBER', 'Member'
        ADMIN = 'ADMIN', 'Admin'
        MANAGER = 'MANAGER', 'Manager'
        STAFF = 'STAFF', 'Staff'
        TENANT = 'TENANT', 'Tenant'
        VENDOR = 'VENDOR', 'Vendor'

    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.VERIFIED,
    )
    provisioned_by_owner = models.BooleanField(default=False)
    verified_by_superuser = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_accounts',
    )
    created_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_accounts',
    )
    delegated_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='delegated_accounts',
    )
    delegated_at = models.DateTimeField(null=True, blank=True)
   
    organizations = models.ManyToManyField(
        'iam.Organization',
        related_name='members',
        blank=True
    )

    @property
    def is_verified(self):
        return self.verification_status == self.VerificationStatus.VERIFIED

    def can_access_platform(self):
        return self.is_active and (self.is_verified or self.is_superuser)
    
    def __str__(self):
        return self.username


class UserOnboardingEvent(BaseModel):
    class EventType(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        VERIFIED = 'VERIFIED', 'Verified'
        OWNER_ASSIGNED = 'OWNER_ASSIGNED', 'Owner Assigned'
        MEMBER_DELEGATED = 'MEMBER_DELEGATED', 'Member Delegated'

    account = models.ForeignKey('iam.User', on_delete=models.CASCADE, related_name='onboarding_events')
    actor = models.ForeignKey('iam.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='account_actions')
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} -> {self.account.username}"
