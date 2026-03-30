#!/usr/bin/env python
"""
Test script for email notifications
Run: python manage.py shell < test-emails.py
"""

from django.contrib.auth import get_user_model
from events.models import Event, EventRegistration
from events.tasks import (
    send_registration_confirmation,
    send_event_reminder,
    send_event_update_notification,
    send_event_cancellation
)
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

# Create test user if not exists
user, created = User.objects.get_or_create(
    email='test@example.com',
    defaults={
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User'
    }
)
if created:
    user.set_password('test123')
    user.save()
    print(f"✓ Created test user: {user.email}")
else:
    print(f"✓ Using existing user: {user.email}")

# Create test event
event, created = Event.objects.get_or_create(
    title='Test Event for Email',
    defaults={
        'description': 'This is a test event to verify email notifications',
        'date': timezone.now() + timedelta(days=2),
        'location': 'Test Location, Main Street',
        'organizer': user,
        'category': 'tech',
        'max_attendees': 50,
        'is_published': True
    }
)
if created:
    print(f"✓ Created test event: {event.title}")
else:
    print(f"✓ Using existing event: {event.title}")

# Create registration
registration, created = EventRegistration.objects.get_or_create(
    event=event,
    user=user,
    defaults={
        'status': EventRegistration.StatusChoices.CONFIRMED
    }
)
if created:
    print(f"✓ Created registration for {user.email}")
else:
    print(f"✓ Registration already exists")

print("\n" + "="*60)
print("TESTING EMAIL TASKS")
print("="*60)

# Test 1: Registration confirmation
print("\n1. Testing registration confirmation email...")
result = send_registration_confirmation.delay(user.id, event.id)
print(f"   Task ID: {result.id}")
print(f"   Result: {result.get(timeout=10)}")

# Test 2: Event reminder
print("\n2. Testing event reminder email...")
result = send_event_reminder.delay(event.id)
print(f"   Task ID: {result.id}")
print(f"   Result: {result.get(timeout=10)}")

# Test 3: Event update notification
print("\n3. Testing event update notification...")
changes = "• Date changed to: March 15, 2024\n• Location updated"
result = send_event_update_notification.delay(event.id, changes)
print(f"   Task ID: {result.id}")
print(f"   Result: {result.get(timeout=10)}")

# Test 4: Event cancellation
print("\n4. Testing event cancellation email...")
result = send_event_cancellation.delay(event.id)
print(f"   Task ID: {result.id}")
print(f"   Result: {result.get(timeout=10)}")

print("\n" + "="*60)
print("✅ ALL EMAIL TESTS COMPLETED")
print("="*60)
print("\nCheck your email inbox (or console if using console backend)")
print("If using Docker, check logs: docker-compose logs -f celery")
