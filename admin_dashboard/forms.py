# admin_dashboard/forms.py
from django import forms
from .models import SystemSettings, Dispute
from users.models import CustomUser

class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            'base_price_per_kg',
            'tier1_max_weight', 'tier1_price_per_kg',
            'tier2_max_weight', 'tier2_price_per_kg',
            'tier3_price_per_kg',
            'platform_fee_percentage',
        ]

class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ['subject', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class DisputeResponseForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ['status', 'resolution']
        widgets = {
            'resolution': forms.Textarea(attrs={'rows': 4}),
        }

class UserFilterForm(forms.Form):
    user_type = forms.ChoiceField(
        choices=[('', 'All')] + list(CustomUser.USER_TYPE_CHOICES),
        required=False
    )
    is_verified = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Verified'), ('False', 'Not Verified')],
        required=False
    )
    date_joined_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_joined_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )