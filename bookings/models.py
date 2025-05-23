# bookings/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from itineraries.models import Itinerary
import uuid


class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_bookings')
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='bookings')
    package_description = models.TextField()
    package_weight = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    package_dimensions = models.CharField(max_length=100, help_text="Format: LxWxH in cm")
    special_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.id} - {self.sender.username} via {self.itinerary.traveler.username}"


class PackageRequest(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='package_requests')
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    preferred_date = models.DateField()
    package_description = models.TextField()
    package_weight = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    package_dimensions = models.CharField(max_length=100, help_text="Format: LxWxH in cm")
    special_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    price_offer = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Package Request {self.id} - {self.sender.username}: {self.origin} to {self.destination}"