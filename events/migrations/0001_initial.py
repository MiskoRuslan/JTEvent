# Generated migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('date', models.DateTimeField()),
                ('location', models.CharField(max_length=300)),
                ('category', models.CharField(choices=[('conference', 'Conference'), ('workshop', 'Workshop'), ('seminar', 'Seminar'), ('meetup', 'Meetup'), ('webinar', 'Webinar'), ('social', 'Social'), ('sports', 'Sports'), ('music', 'Music'), ('arts', 'Arts'), ('tech', 'Tech'), ('business', 'Business'), ('other', 'Other')], max_length=20)),
                ('max_attendees', models.PositiveIntegerField(blank=True, help_text='Leave empty for unlimited attendees', null=True)),
                ('cover_image', models.ImageField(blank=True, null=True, upload_to='events/covers/')),
                ('tags', models.CharField(blank=True, help_text='Comma-separated tags', max_length=200)),
                ('is_published', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organizer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organized_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date'],
                'indexes': [models.Index(fields=['date'], name='events_even_date_idx'), models.Index(fields=['category'], name='events_even_categor_idx'), models.Index(fields=['is_published'], name='events_even_is_publ_idx')],
            },
        ),
        migrations.CreateModel(
            name='EventRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('confirmed', 'Confirmed'), ('pending', 'Pending'), ('waitlist', 'Waitlist'), ('cancelled', 'Cancelled')], default='confirmed', max_length=20)),
                ('registered_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['registered_at'],
                'unique_together': {('event', 'user')},
            },
        ),
    ]
