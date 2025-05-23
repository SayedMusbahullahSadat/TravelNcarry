# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('traveler', 'Traveler'),
        ('sender', 'Sender'),
        ('admin', 'Admin'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='traveler')
    phone_number = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    average_rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    is_verified = models.BooleanField(default=False)
    # stripe_account_id field removed

    def __str__(self):
        return self.email

class Rating(models.Model):
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings_given')
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings_received')
    # Change this line
    booking_id = models.UUIDField()  # Change from IntegerField to UUIDField
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'booking_id')