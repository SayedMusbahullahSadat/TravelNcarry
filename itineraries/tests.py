# itineraries/tests.py
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal

from users.models import CustomUser
from .models import Itinerary
from bookings.models import Booking


class ItineraryModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a test user
        cls.traveler = CustomUser.objects.create_user(
            username='testtraveler',
            email='traveler@example.com',
            password='password123',
            user_type='traveler'
        )

        # Set up test dates
        today = timezone.now().date()
        cls.tomorrow = today + timedelta(days=1)
        cls.day_after = today + timedelta(days=2)

        # Create a test itinerary
        cls.itinerary = Itinerary.objects.create(
            traveler=cls.traveler,
            origin='New York',
            destination='London',
            departure_date=cls.tomorrow,
            departure_time=timezone.now().time(),
            arrival_date=cls.day_after,
            arrival_time=timezone.now().time(),
            capacity_kg=Decimal('10.00'),
            status='active'
        )

    def test_itinerary_creation(self):
        """Test that the itinerary was created correctly"""
        self.assertEqual(self.itinerary.origin, 'New York')
        self.assertEqual(self.itinerary.destination, 'London')
        self.assertEqual(self.itinerary.traveler.username, 'testtraveler')
        self.assertEqual(self.itinerary.status, 'active')
        self.assertEqual(self.itinerary.capacity_kg, Decimal('10.00'))

    def test_string_representation(self):
        """Test the string representation of the Itinerary model"""
        expected_string = f"{self.traveler.username}: New York to London on {self.tomorrow}"
        self.assertEqual(str(self.itinerary), expected_string)

    def test_is_in_past(self):
        """Test the is_in_past method returns correctly based on departure date"""
        # Current itinerary should not be in the past
        self.assertFalse(self.itinerary.is_in_past())

        # Create an itinerary with past dates
        past_date = timezone.now().date() - timedelta(days=1)
        past_itinerary = Itinerary.objects.create(
            traveler=self.traveler,
            origin='Boston',
            destination='Chicago',
            departure_date=past_date,
            departure_time=timezone.now().time(),
            arrival_date=past_date,
            arrival_time=timezone.now().time(),
            capacity_kg=Decimal('5.00'),
            status='completed'
        )

        # This itinerary should be in the past
        self.assertTrue(past_itinerary.is_in_past())

    def test_available_capacity(self):
        """Test the available_capacity method returns correct capacity"""
        # Initially should have full capacity
        self.assertEqual(self.itinerary.available_capacity(), float(self.itinerary.capacity_kg))

        # Create a test sender
        sender = CustomUser.objects.create_user(
            username='testsender',
            email='sender@example.com',
            password='password123',
            user_type='sender'
        )

        # Create a booking using 2.5 kg
        booking = Booking.objects.create(
            sender=sender,
            itinerary=self.itinerary,
            package_description='Test Package',
            package_weight=Decimal('2.50'),
            package_dimensions='10x10x10',
            status='confirmed',
            price=Decimal('25.00')
        )

        # Check available capacity is reduced by the booking weight
        expected_capacity = float(self.itinerary.capacity_kg) - float(booking.package_weight)
        self.assertEqual(self.itinerary.available_capacity(), expected_capacity)

        # Add another booking
        booking2 = Booking.objects.create(
            sender=sender,
            itinerary=self.itinerary,
            package_description='Another Test Package',
            package_weight=Decimal('3.50'),
            package_dimensions='20x20x20',
            status='pending',  # Even pending bookings should reduce capacity
            price=Decimal('35.00')
        )

        # Check available capacity is reduced by both bookings
        expected_capacity = float(self.itinerary.capacity_kg) - float(booking.package_weight) - float(
            booking2.package_weight)
        self.assertEqual(self.itinerary.available_capacity(), expected_capacity)

        # Cancelled bookings should not affect capacity
        booking2.status = 'cancelled'
        booking2.save()

        expected_capacity = float(self.itinerary.capacity_kg) - float(booking.package_weight)
        self.assertEqual(self.itinerary.available_capacity(), expected_capacity)