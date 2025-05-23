# itineraries/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Itinerary(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    traveler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='itineraries')
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_date = models.DateField()
    arrival_time = models.TimeField()
    capacity_kg = models.DecimalField(max_digits=5, decimal_places=2)
    package_restrictions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.traveler.username}: {self.origin} to {self.destination} on {self.departure_date}"

    def is_in_past(self):
        departure_datetime = timezone.datetime.combine(
            self.departure_date,
            self.departure_time,
            tzinfo=timezone.get_current_timezone()
        )
        return departure_datetime < timezone.now()

    def available_capacity(self):
        from bookings.models import Booking
        booked_capacity = Booking.objects.filter(
            itinerary=self,
            status__in=['confirmed', 'in_transit', 'pending']
        ).aggregate(total=models.Sum('package_weight'))['total'] or 0
        return float(self.capacity_kg) - float(booked_capacity)


class SavedSearch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    origin = models.CharField(max_length=255, blank=True)
    destination = models.CharField(max_length=255, blank=True)
    departure_date_from = models.DateField(null=True, blank=True)
    departure_date_to = models.DateField(null=True, blank=True)
    min_capacity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_capacity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    verified_only = models.BooleanField(default=False)
    notify = models.BooleanField(default=False)  # Get notified of new matching itineraries
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    def get_search_url(self):
        """Generate a URL with this search's parameters"""
        from django.urls import reverse
        from urllib.parse import urlencode

        base_url = reverse('itinerary_list')
        params = {}

        if self.origin:
            params['origin'] = self.origin
        if self.destination:
            params['destination'] = self.destination
        if self.departure_date_from:
            params['departure_date_from'] = self.departure_date_from.isoformat()
        if self.departure_date_to:
            params['departure_date_to'] = self.departure_date_to.isoformat()
        if self.min_capacity:
            params['min_capacity'] = self.min_capacity
        if self.max_capacity:
            params['max_capacity'] = self.max_capacity
        if self.min_price:
            params['min_price'] = self.min_price
        if self.max_price:
            params['max_price'] = self.max_price
        if self.min_rating:
            params['min_rating'] = self.min_rating
        if self.verified_only:
            params['verified_only'] = 'on'

        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url