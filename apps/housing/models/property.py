from django.db import models
from apps.core.models import BaseModel

class Amenity(BaseModel):
    name = models.CharField(max_length=100)
    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='amenities'
    )

    class Meta:
        verbose_name_plural = "Amenities"
        unique_together = ('organization', 'name')

    def __str__(self):
        return self.name

class Property(BaseModel):
    organization = models.ForeignKey(
        'iam.Organization',
        on_delete=models.CASCADE,
        related_name='properties'
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='properties')
    
    class Meta:
        verbose_name_plural = "Properties"

    def __str__(self):
        return f"{self.name} - {self.city}"
