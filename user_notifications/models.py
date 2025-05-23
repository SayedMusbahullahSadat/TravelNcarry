# user_notifications/models.py
from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    TYPE_CHOICES = (
        ('booking', 'Booking Update'),
        ('payment', 'Payment Update'),
        ('message', 'New Message'),
        ('rating', 'New Rating'),
        ('system', 'System Notification'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} notification for {self.user.username}"