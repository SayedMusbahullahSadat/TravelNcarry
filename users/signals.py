# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import email_confirmed
from .models import CustomUser

@receiver(email_confirmed)
def email_confirmed_(request, email_address, **kwargs):
    """
    Set user as verified when email is confirmed
    """
    user = email_address.user
    if isinstance(user, CustomUser):
        user.is_verified = True
        user.save()