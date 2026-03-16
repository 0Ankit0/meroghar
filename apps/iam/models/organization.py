from django.db import models
from apps.core.models import BaseModel


class Organization(BaseModel):
    """
    Organization/Tenant model for multi-tenancy.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    address = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def owner_membership(self):
        return self.memberships.filter(
            role='OWNER',
            is_active=True,
        ).select_related('user').first()

    def __str__(self):
        return self.name
