from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel


class LeaseRenewal(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        REQUESTED = 'REQUESTED', 'Requested'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    lease = models.ForeignKey('housing.Lease', on_delete=models.CASCADE, related_name='renewals')
    proposed_start_date = models.DateField()
    proposed_end_date = models.DateField()
    proposed_rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    reviewed_by = models.ForeignKey('iam.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_renewals')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    renewal_lease = models.ForeignKey('housing.Lease', on_delete=models.SET_NULL, null=True, blank=True, related_name='source_renewals')

    def approve(self, reviewer):
        new_lease = self.renewal_lease
        if not new_lease:
            new_lease = self.lease.__class__.objects.create(
                organization=self.lease.organization,
                tenant=self.lease.tenant,
                start_date=self.proposed_start_date,
                end_date=self.proposed_end_date,
                rent_amount=self.proposed_rent_amount,
                deposit_amount=self.lease.deposit_amount,
                status=self.lease.__class__.Status.DRAFT,
                terms_and_conditions=self.lease.terms_and_conditions,
            )
            new_lease.units.set(self.lease.units.all())
        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.renewal_lease = new_lease
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'renewal_lease', 'updated_at'])

    def reject(self, reviewer):
        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

    def __str__(self):
        return f"Renewal {self.id} for {self.lease_id}"
