# bookings/forms.py
from django import forms
from .models import Booking, PackageRequest


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'package_description', 'package_weight', 'package_dimensions',
            'special_instructions'
        ]
        widgets = {
            'package_description': forms.Textarea(attrs={'rows': 3}),
            'special_instructions': forms.Textarea(attrs={'rows': 3}),
        }


class PackageRequestForm(forms.ModelForm):
    class Meta:
        model = PackageRequest
        fields = [
            'origin', 'destination', 'preferred_date', 'package_description',
            'package_weight', 'package_dimensions', 'special_instructions', 'price_offer'
        ]
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'package_description': forms.Textarea(attrs={'rows': 3}),
            'special_instructions': forms.Textarea(attrs={'rows': 3}),
        }


class BookingStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['status']
        widgets = {
            'status': forms.Select(),
        }