# itineraries/admin.py
from django.contrib import admin
from .models import Itinerary


class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('traveler', 'origin', 'destination', 'departure_date', 'status', 'available_capacity')
    list_filter = ('status', 'departure_date')
    search_fields = ('origin', 'destination', 'traveler__username')
    readonly_fields = ('created_at', 'updated_at')

    def available_capacity(self, obj):
        return f"{obj.available_capacity()} kg"

    available_capacity.short_description = 'Available Capacity'


admin.site.register(Itinerary, ItineraryAdmin)