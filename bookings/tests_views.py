# bookings/tests_views.py
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid

from users.models import CustomUser
from itineraries.models import Itinerary
from bookings.models import Booking


class BookingViewsTest(TestCase):
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

    def setUp(self):
        # Set up a client for each test
        self.client = Client()

    def test_booking_list_view_unauthorized(self):
        """Test that unauthorized users are redirected from booking list page"""
        # Try to access without logging in
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_booking_list_view_sender(self):
        """Test booking list view for a sender"""
        # Log in as the sender
        self.client.login(username='testsender', password='password123')

        # Access booking list
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)

        # Check context
        self.assertIn('bookings', response.context)
        self.assertEqual(len(response.context['bookings']), 1)
        self.assertEqual(response.context['bookings'][0], self.booking)

    def test_booking_list_view_traveler(self):
        """Test booking list view for a traveler"""
        # Log in as the traveler
        self.client.login(username='testtraveler', password='password123')

        # Access booking list
        response = self.client.get(reverse('booking_list'))
        self.assertEqual(response.status_code, 200)

        # Check context
        self.assertIn('bookings', response.context)
        self.assertEqual(len(response.context['bookings']), 1)
        self.assertEqual(response.context['bookings'][0], self.booking)

    def test_booking_detail_view(self):
        """Test booking detail view for authorized users"""
        # Log in as the sender
        self.client.login(username='testsender', password='password123')

        # Access booking detail
        response = self.client.get(reverse('booking_detail', kwargs={'pk': self.booking.pk}))
        self.assertEqual(response.status_code, 200)

        # Check context
        self.assertIn('booking', response.context)
        self.assertEqual(response.context['booking'], self.booking)

        # Log in as the traveler and check again
        self.client.logout()
        self.client.login(username='testtraveler', password='password123')

        response = self.client.get(reverse('booking_detail', kwargs={'pk': self.booking.pk}))
        self.assertEqual(response.status_code, 200)

    def test_booking_detail_unauthorized(self):
        """Test that unauthorized users cannot access booking details"""
        # Create a different user not associated with the booking
        other_user = CustomUser.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123',
            user_type='sender'
        )

        # Log in as the other user
        self.client.login(username='otheruser', password='password123')

        # Try to access booking detail
        response = self.client.get(reverse('booking_detail', kwargs={'pk': self.booking.pk}))
        self.assertEqual(response.status_code, 403)  # Should be forbidden

    def test_create_booking(self):
        """Test creating a new booking"""
        # Log in as the sender
        self.client.login(username='testsender', password='password123')

        # Prepare booking data
        booking_data = {
            'package_description': 'New Test Package',
            'package_weight': '3.00',
            'package_dimensions': '15x10x5',
            'special_instructions': 'Very fragile, please handle with extra care',
        }

        # Submit the form
        response = self.client.post(
            reverse('create_booking', kwargs={'itinerary_id': self.itinerary.pk}),
            data=booking_data
        )

        # If successful, should redirect to booking detail
        self.assertEqual(response.status_code, 302)

        # Check that a new booking was created
        self.assertEqual(Booking.objects.count(), 2)

        # Get the new booking
        new_booking = Booking.objects.exclude(pk=self.booking.pk).first()

        # Check its attributes
        self.assertEqual(new_booking.sender, self.sender)
        self.assertEqual(new_booking.itinerary, self.itinerary)
        self.assertEqual(new_booking.package_description, 'New Test Package')
        self.assertEqual(new_booking.package_weight, Decimal('3.00'))
        self.assertEqual(new_booking.package_dimensions, '15x10x5')
        self.assertEqual(new_booking.special_instructions, 'Very fragile, please handle with extra care')
        self.assertEqual(new_booking.status, 'pending')

    def test_update_booking_status(self):
        """Test updating booking status (traveler only)"""
        # Log in as the traveler
        self.client.login(username='testtraveler', password='password123')

        # Prepare update data
        update_data = {
            'status': 'confirmed',
        }

        # Submit the form
        response = self.client.post(
            reverse('update_booking_status', kwargs={'pk': self.booking.pk}),
            data=update_data
        )

        # Should redirect to booking detail
        self.assertEqual(response.status_code, 302)

        # Refresh booking from DB
        self.booking.refresh_from_db()

        # Check status was updated
        self.assertEqual(self.booking.status, 'confirmed')

        # Test that sender cannot update status
        self.client.logout()
        self.client.login(username='testsender', password='password123')

        update_data = {
            'status': 'in_transit',
        }

        response = self.client.post(
            reverse('update_booking_status', kwargs={'pk': self.booking.pk}),
            data=update_data
        )

        # Should give an error or redirect
        self.assertNotEqual(response.status_code, 200)

        # Refresh booking from DB
        self.booking.refresh_from_db()

        # Status should remain unchanged
        self.assertEqual(self.booking.status, 'confirmed')

    def test_cancel_booking(self):
        """Test cancelling a booking"""
        # Log in as the sender
        self.client.login(username='testsender', password='password123')

        # Submit cancellation
        response = self.client.post(
            reverse('cancel_booking', kwargs={'pk': self.booking.pk})
        )

        # Should redirect to booking list
        self.assertEqual(response.status_code, 302)

        # Refresh booking from DB
        self.booking.refresh_from_db()

        # Check status was updated to cancelled
        self.assertEqual(self.booking.status, 'cancelled')

    def test_cancel_delivered_booking(self):
        """Test cannot cancel a delivered booking"""
        # Change booking status to delivered
        self.booking.status = 'delivered'
        self.booking.save()

        # Log in as the sender
        self.client.login(username='testsender', password='password123')

        # Try to cancel
        response = self.client.post(
            reverse('cancel_booking', kwargs={'pk': self.booking.pk})
        )

        # Should redirect with an error message
        self.assertEqual(response.status_code, 302)

        # Refresh booking from DB
        self.booking.refresh_from_db()

        # Status should still be delivered
        self.assertEqual(self.booking.status, 'delivered')

    def test_package_request_list_view(self):
        """Test package request list view"""
        # Create a test package request
        from bookings.models import PackageRequest

        package_request = PackageRequest.objects.create(
            sender=self.sender,
            origin='Boston',
            destination='Paris',
            preferred_date=timezone.now().date() + timedelta(days=7),
            package_description='Request Package',
            package_weight=Decimal('4.00'),
            package_dimensions='18x12x8',
            status='open',
            price_offer=Decimal('60.00')
        )

        # Log in as the sender
        self.client.login(username='testsender', password='password123')

        # Access package request list
        response = self.client.get(reverse('package_request_list'))
        self.assertEqual(response.status_code, 200)

        # Check context
        self.assertIn('package_requests', response.context)
        self.assertEqual(len(response.context['package_requests']), 1)
        self.assertEqual(response.context['package_requests'][0], package_request)

        # Log in as the traveler and check they can see open requests
        self.client.logout()
        self.client.login(username='testtraveler', password='password123')

        response = self.client.get(reverse('package_request_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('package_requests', response.context)
        self.assertEqual(len(response.context['package_requests']), 1)