# user_notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from bookings.models import Booking
from payments.models import Payment
from messaging.models import Message
from users.models import Rating
from .services import NotificationService

@receiver(post_save, sender=Booking)
def booking_notification(sender, instance, created, **kwargs):
    """
    Create notifications when a booking is created or updated.
    """
    NotificationService.create_booking_notification(instance)

@receiver(post_save, sender=Payment)
def payment_notification(sender, instance, created, **kwargs):
    """
    Create notifications when a payment is created or updated.
    """
    if instance.status in ['completed', 'refunded']:
        NotificationService.create_payment_notification(instance)

@receiver(post_save, sender=Message)
def message_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a new message is created.
    """
    if created:
        NotificationService.create_message_notification(instance)

@receiver(post_save, sender=Rating)
def rating_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a new rating is created.
    """
    if created:
        NotificationService.create_rating_notification(instance)