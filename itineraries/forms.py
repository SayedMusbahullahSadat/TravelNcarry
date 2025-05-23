# itineraries/forms.py
from django import forms
from django.utils import timezone
from .models import Itinerary


class ItineraryForm(forms.ModelForm):
    class Meta:
        model = Itinerary
        fields = [
            'origin', 'destination', 'departure_date', 'departure_time',
            'arrival_date', 'arrival_time', 'capacity_kg', 'package_restrictions'
        ]
        widgets = {
            'departure_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
            'departure_time': forms.TimeInput(attrs={'type': 'time'}),
            'arrival_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
            'arrival_time': forms.TimeInput(attrs={'type': 'time'}),
            'package_restrictions': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        departure_date = cleaned_data.get('departure_date')
        arrival_date = cleaned_data.get('arrival_date')
        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')

        if departure_date and arrival_date:
            if departure_date > arrival_date:
                raise forms.ValidationError("Arrival date cannot be earlier than departure date.")
            elif departure_date == arrival_date and departure_time and arrival_time:
                if departure_time >= arrival_time:
                    raise forms.ValidationError("Arrival time must be later than departure time on the same day.")

        return cleaned_data


class ItinerarySearchForm(forms.Form):
    origin = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={'placeholder': 'From', 'class': 'form-control'}))
    destination = forms.CharField(required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'To', 'class': 'form-control'}))

    # Date range instead of single date
    departure_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control', 'min': timezone.now().date().isoformat()})
    )
    departure_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control', 'min': timezone.now().date().isoformat()})
    )

    # Weight/capacity filtering
    min_capacity = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Min. Capacity (kg)', 'class': 'form-control', 'min': '0'})
    )
    max_capacity = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Max. Capacity (kg)', 'class': 'form-control', 'min': '0'})
    )

    # Price range filtering
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Min Price ($)', 'class': 'form-control', 'min': '0'})
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Max Price ($)', 'class': 'form-control', 'min': '0'})
    )

    # Traveler rating filter
    min_rating = forms.ChoiceField(
        required=False,
        choices=[('', 'Any Rating')] + [(str(i), f"{i}+ Stars") for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Verified travelers only
    verified_only = forms.BooleanField(required=False)

    # Sorting options
    SORT_CHOICES = [
        ('departure_date', 'Departure Date (Earliest First)'),
        ('-departure_date', 'Departure Date (Latest First)'),
        ('price', 'Price (Low to High)'),
        ('-price', 'Price (High to Low)'),
        ('-traveler__average_rating', 'Traveler Rating'),
        ('-available_capacity', 'Available Capacity')
    ]

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='departure_date',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        departure_date_from = cleaned_data.get('departure_date_from')
        departure_date_to = cleaned_data.get('departure_date_to')

        # Validate date range
        if departure_date_from and departure_date_to and departure_date_from > departure_date_to:
            raise forms.ValidationError("End date cannot be earlier than start date.")

        return cleaned_data