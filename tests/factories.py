"""
Factory classes for testing using factory-boy.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.utils import timezone
from datetime import timedelta
from users.models import User
from events.models import Event, EventRegistration

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        django_get_or_create = ('email',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    bio = factory.Faker('text', max_nb_chars=200)
    is_active = True
    email_verified = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return
        password = extracted or 'testpass123'
        obj.set_password(password)
        obj.save()


class EventFactory(DjangoModelFactory):
    """Factory for creating Event instances."""

    class Meta:
        model = Event

    title = factory.Faker('catch_phrase')
    description = factory.Faker('text', max_nb_chars=500)
    date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=30))
    location = factory.Faker('address')
    organizer = factory.SubFactory(UserFactory)
    category = factory.Faker('random_element', elements=[
        'conference', 'workshop', 'seminar', 'meetup', 'webinar',
        'social', 'sports', 'music', 'arts', 'tech', 'business', 'other'
    ])
    max_attendees = factory.Faker('random_int', min=10, max=200)
    tags = factory.LazyFunction(lambda: ', '.join(fake.words(nb=3)))
    is_published = True
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def past_event(obj, create, extracted, **kwargs):
        """Create a past event if requested."""
        if not create:
            return
        if extracted:
            obj.date = timezone.now() - timedelta(days=10)
            obj.save()


class EventRegistrationFactory(DjangoModelFactory):
    """Factory for creating EventRegistration instances."""

    class Meta:
        model = EventRegistration

    event = factory.SubFactory(EventFactory)
    user = factory.SubFactory(UserFactory)
    status = EventRegistration.StatusChoices.CONFIRMED
    registered_at = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def waitlist(obj, create, extracted, **kwargs):
        """Set status to waitlist if requested."""
        if not create:
            return
        if extracted:
            obj.status = EventRegistration.StatusChoices.WAITLIST
            obj.save()
