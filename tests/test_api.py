"""
API endpoint tests for Event Management application.
"""
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .factories import UserFactory, EventFactory, EventRegistrationFactory
from events.models import Event, EventRegistration


class EventAPITest(APITestCase):
    """Test cases for Event API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_list_events(self):
        """Test listing events."""
        EventFactory.create_batch(5)
        url = reverse('events:event-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    def test_list_events_pagination(self):
        """Test events list pagination."""
        EventFactory.create_batch(15)
        url = reverse('events:event-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Default page size
        self.assertIsNotNone(response.data['next'])

    def test_filter_events_by_category(self):
        """Test filtering events by category."""
        EventFactory.create_batch(3, category='tech')
        EventFactory.create_batch(2, category='music')

        url = reverse('events:event-list')
        response = self.client.get(url, {'category': 'tech'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_search_events(self):
        """Test searching events."""
        EventFactory(title='Python Workshop')
        EventFactory(title='JavaScript Meetup')

        url = reverse('events:event-list')
        response = self.client.get(url, {'search': 'Python'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('Python', response.data['results'][0]['title'])

    def test_retrieve_event(self):
        """Test retrieving a single event."""
        event = EventFactory()
        url = reverse('events:event-detail', kwargs={'pk': event.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], event.id)
        self.assertEqual(response.data['title'], event.title)

    def test_create_event(self):
        """Test creating an event."""
        url = reverse('events:event-list')
        data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'date': (timezone.now() + timedelta(days=30)).isoformat(),
            'location': 'Test Location',
            'category': 'tech',
            'max_attendees': 50,
            'is_published': True
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Event')
        self.assertEqual(response.data['organizer']['id'], self.user.id)

    def test_create_event_unauthenticated(self):
        """Test creating event requires authentication."""
        self.client.force_authenticate(user=None)
        url = reverse('events:event-list')
        data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'date': (timezone.now() + timedelta(days=30)).isoformat(),
            'location': 'Test Location',
            'category': 'tech'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_event(self):
        """Test updating own event."""
        event = EventFactory(organizer=self.user)
        url = reverse('events:event-detail', kwargs={'pk': event.id})
        data = {'title': 'Updated Title'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    def test_update_others_event_forbidden(self):
        """Test can't update other user's event."""
        event = EventFactory(organizer=self.other_user)
        url = reverse('events:event-detail', kwargs={'pk': event.id})
        data = {'title': 'Updated Title'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_event(self):
        """Test deleting own event."""
        event = EventFactory(organizer=self.user)
        url = reverse('events:event-detail', kwargs={'pk': event.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_delete_others_event_forbidden(self):
        """Test can't delete other user's event."""
        event = EventFactory(organizer=self.other_user)
        url = reverse('events:event-detail', kwargs={'pk': event.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_for_event(self):
        """Test registering for an event."""
        event = EventFactory()
        url = reverse('events:event-register', kwargs={'pk': event.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            EventRegistration.objects.filter(event=event, user=self.user).exists()
        )

    def test_register_for_full_event(self):
        """Test registering for full event adds to waitlist."""
        event = EventFactory(max_attendees=1)
        EventRegistrationFactory(event=event)

        url = reverse('events:event-register', kwargs={'pk': event.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        registration = EventRegistration.objects.get(event=event, user=self.user)
        self.assertEqual(registration.status, EventRegistration.StatusChoices.WAITLIST)

    def test_register_twice_fails(self):
        """Test can't register for same event twice."""
        event = EventFactory()
        EventRegistrationFactory(event=event, user=self.user)

        url = reverse('events:event-register', kwargs={'pk': event.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unregister_from_event(self):
        """Test unregistering from an event."""
        event = EventFactory()
        EventRegistrationFactory(event=event, user=self.user)

        url = reverse('events:event-unregister', kwargs={'pk': event.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            EventRegistration.objects.filter(event=event, user=self.user).exists()
        )

    def test_unregister_when_not_registered(self):
        """Test unregistering when not registered."""
        event = EventFactory()
        url = reverse('events:event-unregister', kwargs={'pk': event.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_events(self):
        """Test retrieving user's organized events."""
        EventFactory.create_batch(3, organizer=self.user)
        EventFactory.create_batch(2, organizer=self.other_user)

        url = reverse('events:event-my-events')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_event_attendees_as_organizer(self):
        """Test organizer can view attendees."""
        event = EventFactory(organizer=self.user)
        EventRegistrationFactory.create_batch(5, event=event)

        url = reverse('events:event-attendees', kwargs={'pk': event.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_event_attendees_as_non_organizer(self):
        """Test non-organizer can't view attendees."""
        event = EventFactory(organizer=self.other_user)
        EventRegistrationFactory.create_batch(5, event=event)

        url = reverse('events:event-attendees', kwargs={'pk': event.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EventRegistrationAPITest(APITestCase):
    """Test cases for EventRegistration API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_my_registrations(self):
        """Test retrieving user's registrations."""
        events = EventFactory.create_batch(3)
        for event in events:
            EventRegistrationFactory(event=event, user=self.user)

        url = reverse('events:eventregistration-my-registrations')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_my_registrations_unauthenticated(self):
        """Test my_registrations requires authentication."""
        self.client.force_authenticate(user=None)
        url = reverse('events:eventregistration-my-registrations')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
