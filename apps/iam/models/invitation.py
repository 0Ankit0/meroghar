import secrets
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel


class OrganizationInvitation(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        EXPIRED = 'EXPIRED', 'Expired'
        REVOKED = 'REVOKED', 'Revoked'

    organization = models.ForeignKey('iam.Organization', on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, default='STAFF')
    invited_by = models.ForeignKey('iam.User', on_delete=models.SET_NULL, null=True, related_name='organization_invitations_sent')
    token = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey('iam.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='organization_invitations_accepted')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        unique_together = ('organization', 'email', 'status')

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(16)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        if self.status == self.Status.PENDING and self.expires_at <= timezone.now():
            self.status = self.Status.EXPIRED
        super().save(*args, **kwargs)

    def mark_accepted(self, user):
        self.status = self.Status.ACCEPTED
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_by', 'accepted_at', 'updated_at'])

    def __str__(self):
        return f"{self.email} -> {self.organization.name}"
