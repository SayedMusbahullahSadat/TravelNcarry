# payments/admin.py
from django.contrib import admin
from .models import Payment, Transaction

class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('created_at',)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('booking__sender__username', 'booking__itinerary__traveler__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TransactionInline]

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('payment', 'amount', 'transaction_type', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('payment__booking__sender__username', 'payment__booking__itinerary__traveler__username')
    readonly_fields = ('created_at',)

admin.site.register(Payment, PaymentAdmin)
admin.site.register(Transaction, TransactionAdmin)