from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from icalendar import Calendar, Event as iCalEvent
from django.contrib.auth import get_user_model
from .models import Event, EventRegistration

User = get_user_model()


def create_ics_file(event):
    """Create .ics calendar file for event"""
    cal = Calendar()
    cal.add('prodid', '-//Event Management System//EN')
    cal.add('version', '2.0')

    ical_event = iCalEvent()
    ical_event.add('summary', event.title)
    ical_event.add('dtstart', event.date)
    ical_event.add('dtend', event.date + timedelta(hours=2))
    ical_event.add('description', event.description)
    ical_event.add('location', event.location)
    ical_event.add('organizer', f'MAILTO:{event.organizer.email}')

    cal.add_component(ical_event)
    return cal.to_ical()


@shared_task
def send_registration_confirmation(user_id, event_id):
    try:
        user = User.objects.get(id=user_id)
        event = Event.objects.select_related('organizer').get(id=event_id)

        context = {
            'user': user,
            'event': event,
            'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
        }

        html_content = render_to_string('emails/registration_confirmation.html', context)
        text_content = f"""
        Hi {user.first_name},

        Thank you for registering for {event.title}!

        Event Details:
        - Date: {event.date.strftime('%B %d, %Y at %I:%M %p')}
        - Location: {event.location}
        - Organizer: {event.organizer.get_full_name()}

        We look forward to seeing you there!

        Best regards,
        Event Management Team
        """

        email = EmailMultiAlternatives(
            subject=f'Registration Confirmed: {event.title}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")

        ics_file = create_ics_file(event)
        email.attach('event.ics', ics_file, 'text/calendar')

        email.send()
        return f'Confirmation email sent to {user.email}'
    except Exception as e:
        return f'Error sending confirmation email: {str(e)}'


@shared_task
def send_event_reminder(event_id):
    try:
        event = Event.objects.select_related('organizer').get(id=event_id)
        registrations = EventRegistration.objects.filter(
            event=event,
            status=EventRegistration.StatusChoices.CONFIRMED
        ).select_related('user')

        emails_sent = 0
        for registration in registrations:
            user = registration.user

            context = {
                'user': user,
                'event': event,
                'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
            }

            html_content = render_to_string('emails/event_reminder.html', context)
            text_content = f"""
            Hi {user.first_name},

            This is a reminder that you're registered for {event.title}, which starts in 24 hours!

            Event Details:
            - Date: {event.date.strftime('%B %d, %Y at %I:%M %p')}
            - Location: {event.location}

            See you there!

            Best regards,
            Event Management Team
            """

            email = EmailMultiAlternatives(
                subject=f'Reminder: {event.title} - Tomorrow!',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            emails_sent += 1

        return f'Reminder sent to {emails_sent} attendees'
    except Exception as e:
        return f'Error sending reminders: {str(e)}'


@shared_task
def send_event_update_notification(event_id, changes):
    try:
        event = Event.objects.select_related('organizer').get(id=event_id)
        registrations = EventRegistration.objects.filter(
            event=event,
            status__in=[EventRegistration.StatusChoices.CONFIRMED, EventRegistration.StatusChoices.WAITLIST]
        ).select_related('user')

        emails_sent = 0
        for registration in registrations:
            user = registration.user

            context = {
                'user': user,
                'event': event,
                'changes': changes,
                'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
            }

            html_content = render_to_string('emails/event_update.html', context)
            text_content = f"""
            Hi {user.first_name},

            The event "{event.title}" has been updated.

            Changes:
            {changes}

            Event Details:
            - Date: {event.date.strftime('%B %d, %Y at %I:%M %p')}
            - Location: {event.location}

            Best regards,
            Event Management Team
            """

            email = EmailMultiAlternatives(
                subject=f'Event Update: {event.title}',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            emails_sent += 1

        return f'Update notification sent to {emails_sent} attendees'
    except Exception as e:
        return f'Error sending update notifications: {str(e)}'


@shared_task
def send_event_cancellation(event_id):
    try:
        event = Event.objects.select_related('organizer').get(id=event_id)
        registrations = EventRegistration.objects.filter(
            event=event,
            status__in=[EventRegistration.StatusChoices.CONFIRMED, EventRegistration.StatusChoices.WAITLIST]
        ).select_related('user')

        emails_sent = 0
        for registration in registrations:
            user = registration.user

            context = {
                'user': user,
                'event': event,
                'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
            }

            html_content = render_to_string('emails/event_cancellation.html', context)
            text_content = f"""
            Hi {user.first_name},

            We regret to inform you that the event "{event.title}" has been cancelled.

            Event Details:
            - Date: {event.date.strftime('%B %d, %Y at %I:%M %p')}
            - Location: {event.location}

            We apologize for any inconvenience this may cause.

            Best regards,
            Event Management Team
            """

            email = EmailMultiAlternatives(
                subject=f'Event Cancelled: {event.title}',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            emails_sent += 1

        return f'Cancellation notification sent to {emails_sent} attendees'
    except Exception as e:
        return f'Error sending cancellation notifications: {str(e)}'


@shared_task
def check_upcoming_events():
    """Check for events that need reminders sent (24 hours before)"""
    now = timezone.now()
    reminder_time = now + timedelta(hours=24)
    reminder_window_start = reminder_time - timedelta(minutes=30)
    reminder_window_end = reminder_time + timedelta(minutes=30)

    upcoming_events = Event.objects.filter(
        date__gte=reminder_window_start,
        date__lte=reminder_window_end,
        is_published=True
    )

    reminders_sent = 0
    for event in upcoming_events:
        send_event_reminder.delay(event.id)
        reminders_sent += 1

    return f'Scheduled {reminders_sent} reminder tasks'
