# itineraries/serializers.py
from rest_framework import serializers
from .models import Itinerary


class ItinerarySerializer(serializers.ModelSerializer):
    traveler_username = serializers.ReadOnlyField(source='traveler.username')
    available_capacity = serializers.SerializerMethodField()

    class Meta:
        model = Itinerary
        fields = [
            'id', 'traveler', 'traveler_username', 'origin', 'destination',
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'capacity_kg', 'package_restrictions', 'status', 'available_capacity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'traveler', 'traveler_username', 'created_at', 'updated_at']

    def get_available_capacity(self, obj):
        return obj.available_capacity()