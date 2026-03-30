"""
Celery task tests for Event Management application.
"""
from django.test import TestCase
from django.core import mail
from django.utils import timezone
from unittest.mock import patch, Mock
from datetime import timedelta
from .factories import UserFactory, EventFactory, EventRegistrationFactory
from events.tasks import (
    send_registration_confirmation,
    send_event_reminder,
    send_event_update_notification,
    send_event_cancellation,
    check_upcoming_events
)


class TaskTestCase(TestCase):
    """Base test case for Celery tasks."""

    def setUp(self):
        self.user = UserFactory()
        self.event = EventFactory(
            date=timezone.now() + timedelta(days=30)
        )
        self.registration = EventRegistrationFactory(
            user=self.user,
            event=self.event
        )


class RegistrationConfirmationTaskTest(TaskTestCase):
    """Test registration confirmation email task."""

    def test_send_registration_confirmation(self):
        """Test sending registration confirmation email."""
        result = send_registration_confirmation(self.user.id, self.event.id)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn(self.event.title, email.subject)
        self.assertIn('confirmed', email.subject.lower())

    def test_send_confirmation_with_invalid_user(self):
        """Test sending confirmation with invalid user ID."""
        result = send_registration_confirmation(99999, self.event.id)
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_confirmation_with_invalid_event(self):
        """Test sending confirmation with invalid event ID."""
        result = send_registration_confirmation(self.user.id, 99999)
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirmation_email_has_ics_attachment(self):
        """Test confirmation email includes .ics calendar file."""
        send_registration_confirmation(self.user.id, self.event.id)

        email = mail.outbox[0]
        self.assertEqual(len(email.attachments), 1)
        filename, content, mimetype = email.attachments[0]
        self.assertTrue(filename.endswith('.ics'))
        self.assertEqual(mimetype, 'text/calendar')


class EventReminderTaskTest(TaskTestCase):
    """Test event reminder email task."""

    def test_send_event_reminder(self):
        """Test sending event reminder email."""
        result = send_event_reminder(self.user.id, self.event.id)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn(self.event.title, email.subject)
        self.assertIn('reminder', email.subject.lower())

    def test_reminder_email_content(self):
        """Test reminder email contains event details."""
        send_event_reminder(self.user.id, self.event.id)

        email = mail.outbox[0]
        body = email.body
        self.assertIn(self.event.title, body)
        self.assertIn(self.event.location, body)

    def test_send_reminder_with_invalid_ids(self):
        """Test sending reminder with invalid IDs."""
        result = send_event_reminder(99999, 99999)
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)


class EventUpdateNotificationTaskTest(TaskTestCase):
    """Test event update notification email task."""

    def test_send_update_notification(self):
        """Test sending update notification email."""
        changes = {'location': 'New Location', 'date': 'New Date'}
        result = send_event_update_notification(self.event.id, changes)

        self.assertTrue(result)
        # Email sent to all attendees
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('updated', email.subject.lower())

    def test_update_notification_contains_changes(self):
        """Test update notification contains change details."""
        changes = {'location': 'New Location'}
        send_event_update_notification(self.event.id, changes)

        email = mail.outbox[0]
        body = email.body
        self.assertIn('location', body.lower())
        self.assertIn('New Location', body)

    def test_send_update_to_multiple_attendees(self):
        """Test update notification sent to all attendees."""
        # Create more registrations
        EventRegistrationFactory.create_batch(3, event=self.event)

        changes = {'location': 'New Location'}
        send_event_update_notification(self.event.id, changes)

        # Should send 4 emails total (including setUp registration)
        self.assertEqual(len(mail.outbox), 4)


class EventCancellationTaskTest(TaskTestCase):
    """Test event cancellation email task."""

    def test_send_cancellation_email(self):
        """Test sending cancellation email."""
        reason = 'Due to unforeseen circumstances'
        result = send_event_cancellation(self.event.id, reason)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('cancelled', email.subject.lower())

    def test_cancellation_includes_reason(self):
        """Test cancellation email includes reason."""
        reason = 'Weather conditions'
        send_event_cancellation(self.event.id, reason)

        email = mail.outbox[0]
        self.assertIn(reason, email.body)

    def test_cancellation_to_all_attendees(self):
        """Test cancellation sent to all attendees."""
        EventRegistrationFactory.create_batch(3, event=self.event)

        send_event_cancellation(self.event.id, 'Test reason')
        self.assertEqual(len(mail.outbox), 4)


class CheckUpcomingEventsTaskTest(TestCase):
    """Test check upcoming events periodic task."""

    @patch('events.tasks.send_event_reminder.delay')
    def test_check_upcoming_events(self, mock_send_reminder):
        """Test check_upcoming_events sends reminders for events in 24h."""
        # Create event in 24 hours
        tomorrow = timezone.now() + timedelta(hours=24)
        event = EventFactory(date=tomorrow)
        registration = EventRegistrationFactory(event=event)

        # Create event in 48 hours (should not trigger)
        event2 = EventFactory(date=timezone.now() + timedelta(hours=48))
        EventRegistrationFactory(event=event2)

        check_upcoming_events()

        # Should only send reminder for first event
        mock_send_reminder.assert_called_once()
        call_args = mock_send_reminder.call_args[0]
        self.assertEqual(call_args[0], registration.user.id)
        self.assertEqual(call_args[1], event.id)

    @patch('events.tasks.send_event_reminder.delay')
    def test_check_upcoming_events_no_events(self, mock_send_reminder):
        """Test check_upcoming_events when no events are upcoming."""
        # Create event in 7 days
        EventFactory(date=timezone.now() + timedelta(days=7))

        check_upcoming_events()

        mock_send_reminder.assert_not_called()

    @patch('events.tasks.send_event_reminder.delay')
    def test_check_upcoming_events_multiple_attendees(self, mock_send_reminder):
        """Test reminders sent to multiple attendees."""
        tomorrow = timezone.now() + timedelta(hours=24)
        event = EventFactory(date=tomorrow)
        EventRegistrationFactory.create_batch(3, event=event)

        check_upcoming_events()

        # Should send 3 reminders
        self.assertEqual(mock_send_reminder.call_count, 3)

    @patch('events.tasks.send_event_reminder.delay')
    def test_check_upcoming_events_only_confirmed(self, mock_send_reminder):
        """Test reminders only sent to confirmed registrations."""
        tomorrow = timezone.now() + timedelta(hours=24)
        event = EventFactory(date=tomorrow)

        # Confirmed registration
        EventRegistrationFactory(event=event, status='confirmed')

        # Waitlist registration (should not get reminder)
        EventRegistrationFactory(event=event, status='waitlist')

        # Cancelled registration (should not get reminder)
        EventRegistrationFactory(event=event, status='cancelled')

        check_upcoming_events()

        # Should only send 1 reminder (to confirmed)
        mock_send_reminder.assert_called_once()
