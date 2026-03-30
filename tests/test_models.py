"""
Model tests for Event Management application.
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .factories import UserFactory, EventFactory, EventRegistrationFactory
from events.models import Event, EventRegistration


class UserModelTest(TestCase):
    """Test cases for User model."""

    def setUp(self):
        self.user = UserFactory()

    def test_user_creation(self):
        """Test user is created successfully."""
        self.assertIsNotNone(self.user.id)
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.email_verified)

    def test_user_email_unique(self):
        """Test email uniqueness constraint."""
        with self.assertRaises(Exception):
            UserFactory(email=self.user.email)

    def test_user_full_name(self):
        """Test full_name property."""
        expected = f"{self.user.first_name} {self.user.last_name}"
        self.assertEqual(self.user.full_name, expected)

    def test_user_str(self):
        """Test string representation."""
        self.assertEqual(str(self.user), self.user.email)


class EventModelTest(TestCase):
    """Test cases for Event model."""

    def setUp(self):
        self.organizer = UserFactory()
        self.event = EventFactory(organizer=self.organizer, max_attendees=50)

    def test_event_creation(self):
        """Test event is created successfully."""
        self.assertIsNotNone(self.event.id)
        self.assertEqual(self.event.organizer, self.organizer)
        self.assertTrue(self.event.is_published)

    def test_event_str(self):
        """Test string representation."""
        self.assertEqual(str(self.event), self.event.title)

    def test_attendees_count_property(self):
        """Test attendees_count property."""
        self.assertEqual(self.event.attendees_count, 0)

        # Add registrations
        EventRegistrationFactory.create_batch(3, event=self.event)
        self.assertEqual(self.event.attendees_count, 3)

    def test_available_spots_property(self):
        """Test available_spots property."""
        self.assertEqual(self.event.available_spots, 50)

        # Add registrations
        EventRegistrationFactory.create_batch(10, event=self.event)
        self.assertEqual(self.event.available_spots, 40)

    def test_available_spots_unlimited(self):
        """Test available_spots when max_attendees is None."""
        event = EventFactory(max_attendees=None)
        self.assertIsNone(event.available_spots)

    def test_is_full_property(self):
        """Test is_full property."""
        self.assertFalse(self.event.is_full)

        # Fill event
        EventRegistrationFactory.create_batch(50, event=self.event)
        self.assertTrue(self.event.is_full)

    def test_is_full_unlimited_event(self):
        """Test is_full for unlimited events."""
        event = EventFactory(max_attendees=None)
        EventRegistrationFactory.create_batch(100, event=event)
        self.assertFalse(event.is_full)

    def test_tags_list_property(self):
        """Test tags_list property."""
        self.event.tags = 'tech, networking, startup'
        self.event.save()
        expected = ['tech', 'networking', 'startup']
        self.assertEqual(self.event.tags_list, expected)

    def test_tags_list_empty(self):
        """Test tags_list when tags is empty."""
        self.event.tags = ''
        self.event.save()
        self.assertEqual(self.event.tags_list, [])


class EventRegistrationModelTest(TestCase):
    """Test cases for EventRegistration model."""

    def setUp(self):
        self.user = UserFactory()
        self.event = EventFactory(max_attendees=2)

    def test_registration_creation(self):
        """Test registration is created successfully."""
        registration = EventRegistrationFactory(user=self.user, event=self.event)
        self.assertIsNotNone(registration.id)
        self.assertEqual(registration.status, EventRegistration.StatusChoices.CONFIRMED)

    def test_registration_str(self):
        """Test string representation."""
        registration = EventRegistrationFactory(user=self.user, event=self.event)
        expected = f"{self.user.email} - {self.event.title}"
        self.assertEqual(str(registration), expected)

    def test_unique_together_constraint(self):
        """Test user can't register for same event twice."""
        EventRegistrationFactory(user=self.user, event=self.event)
        with self.assertRaises(Exception):
            EventRegistrationFactory(user=self.user, event=self.event)

    def test_auto_waitlist_when_full(self):
        """Test automatic waitlist when event is full."""
        # Fill event
        EventRegistrationFactory.create_batch(2, event=self.event)
        self.assertTrue(self.event.is_full)

        # New registration should go to waitlist
        registration = EventRegistration(user=self.user, event=self.event)
        registration.save()
        self.assertEqual(registration.status, EventRegistration.StatusChoices.WAITLIST)

    def test_confirmed_status_when_spots_available(self):
        """Test confirmed status when spots are available."""
        registration = EventRegistration(user=self.user, event=self.event)
        registration.save()
        self.assertEqual(registration.status, EventRegistration.StatusChoices.CONFIRMED)

    def test_unlimited_event_no_waitlist(self):
        """Test unlimited events don't use waitlist."""
        event = EventFactory(max_attendees=None)
        EventRegistrationFactory.create_batch(100, event=event)

        registration = EventRegistration(user=self.user, event=event)
        registration.save()
        self.assertEqual(registration.status, EventRegistration.StatusChoices.CONFIRMED)

    def test_ordering(self):
        """Test registrations are ordered by registered_at."""
        reg1 = EventRegistrationFactory(
            event=self.event,
            registered_at=timezone.now() - timedelta(hours=2)
        )
        reg2 = EventRegistrationFactory(
            event=self.event,
            registered_at=timezone.now() - timedelta(hours=1)
        )

        registrations = EventRegistration.objects.all()
        self.assertEqual(registrations[0], reg1)
        self.assertEqual(registrations[1], reg2)
