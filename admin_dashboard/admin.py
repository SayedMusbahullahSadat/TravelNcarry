# admin_dashboard/admin.py
from django.contrib import admin
from .models import SystemSettings, Dispute
from users.models import CustomUser
from bookings.models import Booking
from itineraries.models import Itinerary
from payments.models import Payment
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'base_price_per_kg', 'platform_fee_percentage', 'updated_at')
    fieldsets = (
        ('Pricing Tiers', {
            'fields': (
                'base_price_per_kg',
                'tier1_max_weight', 'tier1_price_per_kg',
                'tier2_max_weight', 'tier2_price_per_kg',
                'tier3_price_per_kg',
            ),
        }),
        ('Platform Fees', {
            'fields': ('platform_fee_percentage',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

class DisputeAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'booking', 'created_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'description', 'booking__id', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('booking', 'created_by', 'assigned_to', 'subject', 'status'),
        }),
        ('Details', {
            'fields': ('description', 'resolution'),
        }),
    )

admin.site.register(SystemSettings, SystemSettingsAdmin)
admin.site.register(Dispute, DisputeAdmin)