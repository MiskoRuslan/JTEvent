"""
Management command to generate sample data for demo purposes.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from faker import Faker
from users.models import User
from events.models import Event, EventRegistration
import random

fake = Faker()


class Command(BaseCommand):
    help = 'Generate realistic sample events and users for demo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create'
        )
        parser.add_argument(
            '--events',
            type=int,
            default=30,
            help='Number of events to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating'
        )

    def handle(self, *args, **options):
        users_count = options['users']
        events_count = options['events']
        clear = options['clear']

        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            EventRegistration.objects.all().delete()
            Event.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Data cleared'))

        self.stdout.write(f'Creating {users_count} users...')
        users = self.create_users(users_count)
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} users'))

        self.stdout.write(f'Creating {events_count} events...')
        events = self.create_events(events_count, users)
        self.stdout.write(self.style.SUCCESS(f'Created {len(events)} events'))

        self.stdout.write('Creating event registrations...')
        registrations = self.create_registrations(events, users)
        self.stdout.write(self.style.SUCCESS(f'Created {len(registrations)} registrations'))

        self.stdout.write(self.style.SUCCESS('Sample data generation complete!'))
        self.stdout.write(f'Summary:')
        self.stdout.write(f'  - Users: {len(users)}')
        self.stdout.write(f'  - Events: {len(events)}')
        self.stdout.write(f'  - Registrations: {len(registrations)}')

    def create_users(self, count):
        """Create sample users."""
        users = []
        for i in range(count):
            username = fake.user_name() + str(i)
            email = f'{username}@example.com'

            user = User.objects.create_user(
                username=username,
                email=email,
                password='demo123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                bio=fake.text(max_nb_chars=200),
                email_verified=True
            )
            users.append(user)

        return users

    def create_events(self, count, users):
        """Create sample events."""
        categories = [
            'conference', 'workshop', 'seminar', 'meetup', 'webinar',
            'social', 'sports', 'music', 'arts', 'tech', 'business'
        ]

        event_templates = {
            'tech': [
                'Python {adj} Workshop',
                'JavaScript {adj} Meetup',
                'AI and Machine Learning {adj}',
                'Cloud Computing {adj}',
                'Cybersecurity {adj}',
                'Web Development {adj}',
                'DevOps {adj} Conference'
            ],
            'business': [
                'Startup {adj} Summit',
                'Entrepreneurship {adj}',
                'Marketing {adj} Workshop',
                'Leadership {adj} Seminar',
                'Networking {adj} Event'
            ],
            'music': [
                'Live {adj} Concert',
                'Jazz {adj} Night',
                'Classical Music {adj}',
                'Rock {adj} Festival'
            ],
            'sports': [
                '{adj} Marathon',
                'Fitness {adj} Challenge',
                'Yoga {adj} Session',
                'Basketball {adj} Tournament'
            ],
            'arts': [
                'Art {adj} Exhibition',
                'Photography {adj} Workshop',
                'Theater {adj} Performance',
                'Film {adj} Screening'
            ]
        }

        adjectives = ['Essential', 'Advanced', 'Beginner', 'Pro', 'Ultimate', 'Complete', 'Intensive']

        events = []
        now = timezone.now()

        for i in range(count):
            category = random.choice(categories)

            # Generate title
            if category in event_templates:
                title_template = random.choice(event_templates[category])
                title = title_template.format(adj=random.choice(adjectives))
            else:
                title = f'{category.capitalize()} {random.choice(adjectives)} Event'

            # Generate date (20% past, 80% future)
            if random.random() < 0.2:
                # Past event
                days_ago = random.randint(1, 60)
                event_date = now - timedelta(days=days_ago)
            else:
                # Future event (within next 90 days)
                days_ahead = random.randint(1, 90)
                event_date = now + timedelta(days=days_ahead)

            # Generate location
            locations = [
                fake.address(),
                'Zoom Meeting',
                'Google Meet',
                'Microsoft Teams',
                f'{fake.company()} Office',
                f'{fake.street_address()}, {fake.city()}'
            ]

            # Generate tags
            tech_tags = ['python', 'javascript', 'react', 'django', 'ai', 'ml', 'cloud']
            business_tags = ['startup', 'networking', 'leadership', 'innovation']
            all_tags = tech_tags + business_tags + ['professional', 'community', 'learning']
            tags = ', '.join(random.sample(all_tags, k=random.randint(2, 4)))

            event = Event.objects.create(
                title=title,
                description=fake.text(max_nb_chars=800),
                date=event_date,
                location=random.choice(locations),
                organizer=random.choice(users),
                category=category,
                max_attendees=random.choice([None, 20, 50, 100, 200]),
                tags=tags,
                is_published=random.random() > 0.1  # 90% published
            )
            events.append(event)

        return events

    def create_registrations(self, events, users):
        """Create sample event registrations."""
        registrations = []

        for event in events:
            # Skip past events occasionally
            if event.date < timezone.now() and random.random() < 0.3:
                continue

            # Random number of attendees (20-80% of max or random if unlimited)
            if event.max_attendees:
                num_attendees = random.randint(
                    int(event.max_attendees * 0.2),
                    min(int(event.max_attendees * 0.8), len(users))
                )
            else:
                num_attendees = random.randint(5, min(30, len(users)))

            # Select random attendees
            attendees = random.sample(users, k=num_attendees)

            for user in attendees:
                # Skip if user is organizer
                if user == event.organizer:
                    continue

                try:
                    registration = EventRegistration.objects.create(
                        event=event,
                        user=user,
                        registered_at=event.created_at + timedelta(
                            hours=random.randint(1, 48)
                        )
                    )
                    registrations.append(registration)
                except Exception:
                    # Skip if already registered
                    pass

        return registrations
