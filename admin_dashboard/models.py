# admin_dashboard/models.py
from django.db import models
from django.core.validators import MinValueValidator


class SystemSettings(models.Model):
    """Model to store system-wide settings"""
    # Pricing settings
    base_price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0.01)],
        help_text="Base price per kg for package delivery"
    )

    # Weight tiers for pricing (optional additional charges per kg)
    tier1_max_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        validators=[MinValueValidator(0.01)],
        help_text="Maximum weight for tier 1 pricing"
    )
    tier1_price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0.01)],
        help_text="Price per kg for tier 1 weight"
    )

    tier2_max_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0.01)],
        help_text="Maximum weight for tier 2 pricing"
    )
    tier2_price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0.01)],
        help_text="Price per kg for tier 2 weight"
    )

    tier3_price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20.00,
        validators=[MinValueValidator(0.01)],
        help_text="Price per kg for tier 3 weight (above tier 2 max weight)"
    )

    # Platform fee (percentage)
    platform_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0.01)],
        help_text="Platform fee percentage on each transaction"
    )

    # Created and modified timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return f"System Settings (Updated: {self.updated_at})"

    def calculate_price(self, weight):
        """Calculate price based on weight and tier pricing"""
        if weight <= self.tier1_max_weight:
            return weight * self.tier1_price_per_kg
        elif weight <= self.tier2_max_weight:
            return self.tier1_max_weight * self.tier1_price_per_kg + \
                (weight - self.tier1_max_weight) * self.tier2_price_per_kg
        else:
            return self.tier1_max_weight * self.tier1_price_per_kg + \
                (self.tier2_max_weight - self.tier1_max_weight) * self.tier2_price_per_kg + \
                (weight - self.tier2_max_weight) * self.tier3_price_per_kg

    def calculate_platform_fee(self, amount):
        """Calculate platform fee for a given amount"""
        return amount * (self.platform_fee_percentage / 100)

    @classmethod
    def get_settings(cls):
        """Get or create the system settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class Dispute(models.Model):
    """Model for handling disputes between users"""
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='disputes')
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='created_disputes'
    )
    assigned_to = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        related_name='assigned_disputes',
        null=True,
        blank=True
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dispute {self.id} - {self.subject} ({self.status})"