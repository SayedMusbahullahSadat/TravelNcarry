# payments/forms.py
from django import forms
from .models import Payment

class PaymentMethodForm(forms.Form):
    card_number = forms.CharField(max_length=19, required=True, widget=forms.TextInput(attrs={'placeholder': '4242 4242 4242 4242'}))
    expiry_month = forms.ChoiceField(choices=[(str(i), str(i)) for i in range(1, 13)])
    expiry_year = forms.ChoiceField(choices=[(str(i), str(i)) for i in range(2023, 2031)])
    cvc = forms.CharField(max_length=4, min_length=3, required=True, widget=forms.TextInput(attrs={'placeholder': 'CVC'}))
    name_on_card = forms.CharField(max_length=100, required=True)