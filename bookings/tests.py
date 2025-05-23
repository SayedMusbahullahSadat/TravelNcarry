# bookings/tests.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from users.models import CustomUser
from itineraries.models import Itinerary
from .models import Booking, PackageRequest


class BookingModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test users
        cls.traveler = CustomUser.objects.create_user(
            username='testtraveler',
            email='traveler@example.com',
            password='password123',
            user_type='traveler'
        )

        cls.sender = CustomUser.objects.create_user(
            username='testsender',
            email='sender@example.com',
            password='password123',
            user_type='sender'
        )

        # Set up test dates
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)

        # Create a test itinerary
        cls.itinerary = Itinerary.objects.create(
            traveler=cls.traveler,
            origin='New York',
            destination='London',
            departure_date=tomorrow,
            departure_time=timezone.now().time(),
            arrival_date=day_after,
            arrival_time=timezone.now().time(),
            capacity_kg=Decimal('20.00'),
            status='active'
        )

        # Create a test booking
        cls.booking = Booking.objects.create(
            sender=cls.sender,
            itinerary=cls.itinerary,
            package_description='Test Package',
            package_weight=Decimal('5.00'),
            package_dimensions='20x15x10',
            special_instructions='Handle with care',
            status='pending',
            price=Decimal('50.00')
        )

    def test_booking_creation(self):
        """Test that booking was created correctly"""
        self.assertEqual(self.booking.sender, self.sender)
        self.assertEqual(self.booking.itinerary, self.itinerary)
        self.assertEqual(self.booking.package_weight, Decimal('5.00'))
        self.assertEqual(self.booking.status, 'pending')
        self.assertEqual(self.booking.price, Decimal('50.00'))

    def test_string_representation(self):
        """Test the string representation of the Booking model"""
        expected_string = f"Booking {self.booking.id} - {self.sender.username} via {self.traveler.username}"
        self.assertEqual(str(self.booking), expected_string)

    def test_booking_status_transitions(self):
        """Test valid status transitions for a booking"""
        # Start with pending
        self.assertEqual(self.booking.status, 'pending')

        # Transition to confirmed
        self.booking.status = 'confirmed'
        self.booking.save()
        self.assertEqual(self.booking.status, 'confirmed')

        # Transition to in_transit
        self.booking.status = 'in_transit'
        self.booking.save()
        self.assertEqual(self.booking.status, 'in_transit')

        # Transition to delivered
        self.booking.status = 'delivered'
        self.booking.save()
        self.assertEqual(self.booking.status, 'delivered')

    def test_multiple_bookings_against_capacity(self):
        """Test creating multiple bookings against itinerary capacity"""
        # Current available capacity should be original capacity minus first booking
        current_capacity = self.itinerary.available_capacity()
        self.assertEqual(current_capacity, float(self.itinerary.capacity_kg) - float(self.booking.package_weight))

        # Create a second booking
        booking2 = Booking.objects.create(
            sender=self.sender,
            itinerary=self.itinerary,
            package_description='Second Package',
            package_weight=Decimal('7.50'),
            package_dimensions='30x25x15',
            status='pending',
            price=Decimal('75.00')
        )

        # Available capacity should be reduced further
        new_capacity = self.itinerary.available_capacity()
        self.assertEqual(new_capacity, float(self.itinerary.capacity_kg) - float(self.booking.package_weight) - float(
            booking2.package_weight))

        # Should be able to create another booking up to the capacity limit
        remaining_weight = Decimal(str(new_capacity))
        booking3 = Booking.objects.create(
            sender=self.sender,
            itinerary=self.itinerary,
            package_description='Third Package',
            package_weight=remaining_weight,
            package_dimensions='15x15x15',
            status='pending',
            price=Decimal('100.00')
        )

        # Available capacity should now be very close to zero
        final_capacity = self.itinerary.available_capacity()
        self.assertAlmostEqual(final_capacity, 0, places=2)


class PackageRequestModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a test sender
        cls.sender = CustomUser.objects.create_user(
            username='testsender',
            email='sender@example.com',
            password='password123',
            user_type='sender'
        )

        # Create a test package request
        cls.package_request = PackageRequest.objects.create(
            sender=cls.sender,
            origin='Los Angeles',
            destination='Tokyo',
            preferred_date=timezone.now().date() + timedelta(days=5),
            package_description='Electronics',
            package_weight=Decimal('3.00'),
            package_dimensions='25x20x15',
            special_instructions='Fragile items',
            status='open',
            price_offer=Decimal('80.00')
        )

    def test_package_request_creation(self):
        """Test that package request was created correctly"""
        self.assertEqual(self.package_request.sender, self.sender)
        self.assertEqual(self.package_request.origin, 'Los Angeles')
        self.assertEqual(self.package_request.destination, 'Tokyo')
        self.assertEqual(self.package_request.package_weight, Decimal('3.00'))
        self.assertEqual(self.package_request.status, 'open')
        self.assertEqual(self.package_request.price_offer, Decimal('80.00'))

    def test_string_representation(self):
        """Test the string representation of the PackageRequest model"""
        expected_string = f"Package Request {self.package_request.id} - {self.sender.username}: Los Angeles to Tokyo"
        self.assertEqual(str(self.package_request), expected_string)

    def test_status_change(self):
        """Test status transitions for package requests"""
        # Start with open
        self.assertEqual(self.package_request.status, 'open')

        # Transition to accepted
        self.package_request.status = 'accepted'
        self.package_request.save()
        self.assertEqual(self.package_request.status, 'accepted')

        # Transition to cancelled
        self.package_request.status = 'cancelled'
        self.package_request.save()
        self.assertEqual(self.package_request.status, 'cancelled')