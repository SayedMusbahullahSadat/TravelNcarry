# bookings/admin.py
from django.contrib import admin
from .models import Booking, PackageRequest


class BookingAdmin(admin.ModelAdmin):
    list_display = ('sender', 'itinerary_info', 'package_weight', 'status', 'price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('sender__username', 'itinerary__origin', 'itinerary__destination')
    readonly_fields = ('created_at', 'updated_at')

    def itinerary_info(self, obj):
        return f"{obj.itinerary.origin} to {obj.itinerary.destination} on {obj.itinerary.departure_date}"

    itinerary_info.short_description = 'Itinerary'


class PackageRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'origin', 'destination', 'preferred_date', 'status', 'price_offer')
    list_filter = ('status', 'preferred_date')
    search_fields = ('sender__username', 'origin', 'destination')
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(Booking, BookingAdmin)
admin.site.register(PackageRequest, PackageRequestAdmin)