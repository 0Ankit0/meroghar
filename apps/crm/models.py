from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Lead(BaseModel):
    class Status(models.TextChoices):
        NEW = 'NEW', _('New')
        CONTACTED = 'CONTACTED', _('Contacted')
        QUALIFIED = 'QUALIFIED', _('Qualified')
        CONVERTED = 'CONVERTED', _('Converted')
        LOST = 'LOST', _('Lost')

    class Source(models.TextChoices):
        WEBSITE = 'WEBSITE', _('Website')
        REFERRAL = 'REFERRAL', _('Referral')
        LISTING_SITE = 'LISTING_SITE', _('Listing Site')
        WALK_IN = 'WALK_IN', _('Walk-in')
        OTHER = 'OTHER', _('Other')

    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='leads'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.WEBSITE
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    
    notes = models.TextField(blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class Showing(BaseModel):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Scheduled')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        NO_SHOW = 'NO_SHOW', _('No Show')

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='showings'
    )
    unit = models.ForeignKey(
        'housing.Unit',
        on_delete=models.CASCADE,
        related_name='showings'
    )
    showing_agent = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='showings'
    )
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Showing: {self.lead} at {self.unit}"


class RentalApplication(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        REVIEW = 'REVIEW', _('Under Review')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        WITHDRAWN = 'WITHDRAWN', _('Withdrawn')

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    unit = models.ForeignKey(
        'housing.Unit',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    
    # Financial Info
    annual_income = models.DecimalField(max_digits=12, decimal_places=2)
    employment_status = models.CharField(max_length=100)
    employer_name = models.CharField(max_length=100, blank=True)
    
    # References (JSON for simplicity or separate model if complex)
    references = models.JSONField(default=list, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    submission_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Application: {self.lead} for {self.unit}"


class LeadFollowUp(BaseModel):
    class Channel(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        PHONE = 'PHONE', 'Phone'
        SMS = 'SMS', 'SMS'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        DONE = 'DONE', 'Done'
        SKIPPED = 'SKIPPED', 'Skipped'

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='follow_ups')
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.EMAIL)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    message = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Follow-up for {self.lead} ({self.channel})"
