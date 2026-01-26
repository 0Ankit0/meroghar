from django.db import models
from django.contrib.auth.models import Permission
from apps.core.models import BaseModel

class OrganizationGroup(BaseModel):
    """
    A group that spans multiple organizations and assigns permissions to users
    within those organizations.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    organizations = models.ManyToManyField(
        'iam.Organization',
        related_name='groups',
        blank=True
    )
    
    members = models.ManyToManyField(
        'iam.User',
        related_name='organization_groups',
        blank=True
    )
    
    permissions = models.ManyToManyField(
        Permission,
        related_name='organization_groups',
        blank=True,
        help_text='Permissions granted to members of this group for the associated organizations.'
    )
    
    def __str__(self):
        return self.name
