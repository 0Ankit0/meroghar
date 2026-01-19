from django.db import models
from apps.core.models import BaseModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Document(BaseModel):
    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    
    # Polymorphic association to link document to any object (Lease, Property, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=36, null=True, blank=True) # UUID support
    content_object = GenericForeignKey('content_type', 'object_id')
    
    uploaded_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    def __str__(self):
        return self.title
