"""
Event models for the Event Management system.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Event(models.Model):
    """
    Event model representing events that users can organize and attend.
    """

    class CategoryChoices(models.TextChoices):
        CONFERENCE = 'conference', _('Conference')
        WORKSHOP = 'workshop', _('Workshop')
        SEMINAR = 'seminar', _('Seminar')
        MEETUP = 'meetup', _('Meetup')
        WEBINAR = 'webinar', _('Webinar')
        SOCIAL = 'social', _('Social')
        SPORTS = 'sports', _('Sports')
        MUSIC = 'music', _('Music')
        ARTS = 'arts', _('Arts')
        TECH = 'tech', _('Technology')
        BUSINESS = 'business', _('Business')
        OTHER = 'other', _('Other')

    title = models.CharField(
        max_length=200,
        help_text=_('Event title')
    )
    description = models.TextField(
        help_text=_('Detailed event description')
    )
    date = models.DateTimeField(
        help_text=_('Event date and time')
    )
    location = models.CharField(
        max_length=300,
        help_text=_('Event location or virtual meeting link')
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_events',
        help_text=_('Event organizer')
    )
    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.OTHER,
        help_text=_('Event category')
    )
    max_attendees = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
        help_text=_('Maximum number of attendees (null for unlimited)')
    )
    cover_image = models.ImageField(
        upload_to='events/covers/',
        null=True,
        blank=True,
        help_text=_('Event cover image')
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Comma-separated tags')
    )
    is_published = models.BooleanField(
        default=True,
        help_text=_('Whether the event is publicly visible')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = _('event')
        verbose_name_plural = _('events')
        indexes = [
            models.Index(fields=['date', 'is_published']),
            models.Index(fields=['category']),
            models.Index(fields=['organizer']),
        ]

    def __str__(self):
        return self.title

    @property
    def attendees_count(self):
        """
        Return the number of confirmed attendees.
        """
        return self.registrations.filter(
            status=EventRegistration.StatusChoices.CONFIRMED
        ).count()

    @property
    def available_spots(self):
        """
        Return the number of available spots.
        Returns None if unlimited.
        """
        if self.max_attendees is None:
            return None
        return max(0, self.max_attendees - self.attendees_count)

    @property
    def is_full(self):
        """
        Check if the event is full.
        """
        if self.max_attendees is None:
            return False
        return self.attendees_count >= self.max_attendees

    @property
    def is_past(self):
        """
        Check if the event date has passed.
        """
        return self.date < timezone.now()

    @property
    def is_upcoming(self):
        """
        Check if the event is upcoming (within next 30 days).
        """
        now = timezone.now()
        thirty_days = now + timezone.timedelta(days=30)
        return now <= self.date <= thirty_days

    def get_tags_list(self):
        """
        Return tags as a list.
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def get_cover_image_url(self):
        """
        Return cover image URL or default banner based on category.
        """
        if self.cover_image:
            return self.cover_image.url
        # Return default banner from static/banners/{category}.png (or .svg as fallback)
        return f'/static/banners/{self.category}.png'


class EventRegistration(models.Model):
    """
    Model representing user registration for events.
    """

    class StatusChoices(models.TextChoices):
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELLED = 'cancelled', _('Cancelled')
        WAITLIST = 'waitlist', _('Waitlist')

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations',
        help_text=_('Event')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_registrations',
        help_text=_('Registered user')
    )
    registered_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Registration timestamp')
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.CONFIRMED,
        help_text=_('Registration status')
    )
    notes = models.TextField(
        blank=True,
        help_text=_('Additional notes or comments')
    )

    class Meta:
        unique_together = [['event', 'user']]
        ordering = ['-registered_at']
        verbose_name = _('event registration')
        verbose_name_plural = _('event registrations')
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.event.title} ({self.status})'

    def save(self, *args, **kwargs):
        """
        Override save to handle waitlist logic.
        """
        if not self.pk:  # New registration
            if self.event.is_full:
                self.status = self.StatusChoices.WAITLIST
        super().save(*args, **kwargs)
