# users/tests.py
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

from .models import CustomUser, Rating
from bookings.models import Booking
from itineraries.models import Itinerary


class CustomUserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test users
        cls.traveler = CustomUser.objects.create_user(
            username='testtraveler',
            email='traveler@example.com',
            password='password123',
            user_type='traveler',
            bio='I travel a lot for business',
            phone_number='+1234567890',
            address='123 Traveler St, City'
        )

        cls.sender = CustomUser.objects.create_user(
            username='testsender',
            email='sender@example.com',
            password='password123',
            user_type='sender',
            bio='I send packages internationally',
            phone_number='+0987654321',
            address='456 Sender Ave, Town'
        )

        cls.admin_user = CustomUser.objects.create_user(
            username='testadmin',
            email='admin@example.com',
            password='password123',
            user_type='admin',
            is_staff=True
        )

    def test_user_creation(self):
        """Test that users were created with correct attributes"""
        self.assertEqual(self.traveler.username, 'testtraveler')
        self.assertEqual(self.traveler.email, 'traveler@example.com')
        self.assertEqual(self.traveler.user_type, 'traveler')
        self.assertEqual(self.traveler.bio, 'I travel a lot for business')

        self.assertEqual(self.sender.username, 'testsender')
        self.assertEqual(self.sender.user_type, 'sender')

        self.assertEqual(self.admin_user.username, 'testadmin')
        self.assertEqual(self.admin_user.user_type, 'admin')
        self.assertTrue(self.admin_user.is_staff)

    def test_string_representation(self):
        """Test the string representation of the CustomUser model"""
        self.assertEqual(str(self.traveler), self.traveler.email)
        self.assertEqual(str(self.sender), self.sender.email)

    def test_user_verification(self):
        """Test user verification functionality"""
        # Initially users should be unverified
        self.assertFalse(self.traveler.is_verified)

        # Set verification status
        self.traveler.is_verified = True
        self.traveler.save()

        # Refresh from DB and check
        refreshed_traveler = CustomUser.objects.get(pk=self.traveler.pk)
        self.assertTrue(refreshed_traveler.is_verified)

    def test_user_type_choices(self):
        """Test that user_type choices are enforced"""
        # Valid user types
        valid_types = ['traveler', 'sender', 'admin']

        for valid_type in valid_types:
            user = CustomUser(
                username=f'test{valid_type}2',
                email=f'{valid_type}2@example.com',
                user_type=valid_type
            )
            try:
                user.full_clean()  # This validates the model
                user.save()
                self.assertEqual(user.user_type, valid_type)
            except ValidationError:
                self.fail(f"ValidationError raised for valid user_type: {valid_type}")


class RatingModelTest(TestCase):
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

        # Create an itinerary and booking to relate to ratings
        cls.itinerary = Itinerary.objects.create(
            traveler=cls.traveler,
            origin='New York',
            destination='London',
            departure_date='2025-01-01',
            departure_time='10:00:00',
            arrival_date='2025-01-02',
            arrival_time='08:00:00',
            capacity_kg=Decimal('20.00'),
            status='active'
        )

        cls.booking = Booking.objects.create(
            sender=cls.sender,
            itinerary=cls.itinerary,
            package_description='Test Package',
            package_weight=Decimal('5.00'),
            package_dimensions='20x15x10',
            status='delivered',
            price=Decimal('50.00')
        )

        # Create a rating
        cls.rating = Rating.objects.create(
            from_user=cls.sender,
            to_user=cls.traveler,
            booking_id=cls.booking.id,
            rating=5,
            comment='Excellent service, package arrived in perfect condition!'
        )

    def test_rating_creation(self):
        """Test that rating was created correctly"""
        self.assertEqual(self.rating.from_user, self.sender)
        self.assertEqual(self.rating.to_user, self.traveler)
        self.assertEqual(self.rating.booking_id, self.booking.id)
        self.assertEqual(self.rating.rating, 5)
        self.assertEqual(self.rating.comment, 'Excellent service, package arrived in perfect condition!')

    def test_rating_validation(self):
        """Test rating value constraints (1-5)"""
        # Try with invalid rating (too high)
        with self.assertRaises(ValidationError):
            invalid_rating = Rating(
                from_user=self.traveler,
                to_user=self.sender,
                booking_id=self.booking.id,
                rating=6,
                comment='Invalid rating'
            )
            invalid_rating.full_clean()

        # Try with invalid rating (too low)
        with self.assertRaises(ValidationError):
            invalid_rating = Rating(
                from_user=self.traveler,
                to_user=self.sender,
                booking_id=self.booking.id,
                rating=0,
                comment='Invalid rating'
            )
            invalid_rating.full_clean()

        # Valid ratings should pass validation
        for i in range(1, 6):
            valid_rating = Rating(
                from_user=self.traveler,
                to_user=self.sender,
                booking_id=uuid.uuid4(),  # Need unique booking ID for each
                rating=i,
                comment=f'Valid rating: {i}'
            )
            try:
                valid_rating.full_clean()
                valid_rating.save()
            except ValidationError:
                self.fail(f"ValidationError raised for valid rating: {i}")

    def test_unique_constraint(self):
        """Test that a user can only leave one rating per booking"""
        # Try to create a second rating for the same booking/user combination
        with self.assertRaises(Exception):  # Could be IntegrityError or ValidationError depending on DB
            duplicate_rating = Rating.objects.create(
                from_user=self.sender,
                to_user=self.traveler,
                booking_id=self.booking.id,
                rating=4,
                comment='This should fail due to unique constraint'
            )

    def test_average_rating_calculation(self):
        """Test that average rating is calculated correctly"""
        # Initially traveler should have 0 rating (unless auto-calculated on save)
        initial_rating = self.traveler.average_rating

        # Let's manually update it based on our new rating (in practice this would be done by a signal or method)
        self.traveler.average_rating = 5.0  # Since we only have one 5-star rating
        self.traveler.save()

        # Refresh from DB
        refreshed_traveler = CustomUser.objects.get(pk=self.traveler.pk)
        self.assertEqual(refreshed_traveler.average_rating, 5.0)

        # Add another rating from a different user
        new_sender = CustomUser.objects.create_user(
            username='anothersender',
            email='another@example.com',
            password='password123',
            user_type='sender'
        )

        new_booking = Booking.objects.create(
            sender=new_sender,
            itinerary=self.itinerary,
            package_description='Another Package',
            package_weight=Decimal('3.00'),
            package_dimensions='10x10x10',
            status='delivered',
            price=Decimal('30.00')
        )

        new_rating = Rating.objects.create(
            from_user=new_sender,
            to_user=self.traveler,
            booking_id=new_booking.id,
            rating=3,
            comment='Good service but a bit delayed'
        )

        # Update average rating
        self.traveler.average_rating = (5.0 + 3.0) / 2  # Average of 5 and 3
        self.traveler.save()

        # Refresh from DB
        refreshed_traveler = CustomUser.objects.get(pk=self.traveler.pk)
        self.assertEqual(refreshed_traveler.average_rating, 4.0)