from django.db import models
from apps.core.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Notification(BaseModel):
    class Type(models.TextChoices):
        INFO = 'INFO', _('Information')
        WARNING = 'WARNING', _('Warning')
        ERROR = 'ERROR', _('Error')
        SUCCESS = 'SUCCESS', _('Success')

    recipient = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INFO
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Optional link to related object
    action_url = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.recipient}"
