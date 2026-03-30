"""
Admin configuration for Event models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
from django.utils import timezone
import csv
from .models import Event, EventRegistration
from .tasks import send_event_update_notification


class EventRegistrationInline(admin.TabularInline):
    """
    Inline admin for EventRegistration within Event admin.
    """
    model = EventRegistration
    extra = 0
    readonly_fields = ['registered_at']
    fields = ['user', 'status', 'registered_at', 'notes']
    can_delete = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin interface for Event model.
    """
    list_display = [
        'title', 'colored_status', 'date', 'category', 'organizer',
        'registration_info', 'is_published', 'created_at'
    ]
    list_filter = [
        'category', 'is_published', 'date', 'created_at',
        ('date', admin.DateFieldListFilter),
    ]
    search_fields = ['title', 'description', 'location', 'tags', 'organizer__email']
    readonly_fields = [
        'created_at', 'updated_at', 'attendees_count',
        'available_spots', 'is_full', 'view_registrations_link'
    ]
    date_hierarchy = 'date'
    inlines = [EventRegistrationInline]
    actions = [
        'export_attendees_csv',
        'send_update_notification',
        'publish_events',
        'unpublish_events',
        'duplicate_events'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'tags')
        }),
        ('Event Details', {
            'fields': ('date', 'location', 'organizer', 'max_attendees', 'cover_image')
        }),
        ('Status', {
            'fields': (
                'is_published', 'attendees_count', 'available_spots',
                'is_full', 'view_registrations_link'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        qs = super().get_queryset(request)
        return qs.select_related('organizer')

    @admin.display(description='Status', ordering='date')
    def colored_status(self, obj):
        """Display colored status badge."""
        if obj.date < timezone.now():
            color = 'gray'
            status = 'Past'
        elif obj.is_full:
            color = 'red'
            status = 'Full'
        else:
            color = 'green'
            status = 'Open'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 12px;">{}</span>',
            color, status
        )

    @admin.display(description='Registrations')
    def registration_info(self, obj):
        """Display registration info with progress bar."""
        count = obj.attendees_count
        max_attendees = obj.max_attendees

        if max_attendees:
            percentage = (count / max_attendees) * 100
            color = 'green' if percentage < 70 else 'orange' if percentage < 90 else 'red'
            return format_html(
                '<div style="width: 100px;">'
                '<div style="background-color: #f0f0f0; border-radius: 3px; overflow: hidden;">'
                '<div style="background-color: {}; width: {}%; height: 20px; '
                'display: flex; align-items: center; justify-content: center; color: white; '
                'font-size: 11px; font-weight: bold;">{}/{}</div>'
                '</div></div>',
                color, percentage, count, max_attendees
            )
        else:
            return format_html(
                '<span style="font-weight: bold;">{}</span> (Unlimited)',
                count
            )

    @admin.display(description='Registrations')
    def view_registrations_link(self, obj):
        """Link to view registrations."""
        url = reverse('admin:events_eventregistration_changelist')
        return format_html(
            '<a href="{}?event__id__exact={}" class="button">View Registrations</a>',
            url, obj.id
        )

    @admin.action(description='Export attendees to CSV')
    def export_attendees_csv(self, request, queryset):
        """Export attendees of selected events to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="event_attendees.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Event Title', 'Event Date', 'Attendee Name', 'Attendee Email',
            'Registration Status', 'Registered At'
        ])

        for event in queryset:
            registrations = event.eventregistration_set.select_related('user')
            for reg in registrations:
                writer.writerow([
                    event.title,
                    event.date.strftime('%Y-%m-%d %H:%M'),
                    reg.user.full_name,
                    reg.user.email,
                    reg.get_status_display(),
                    reg.registered_at.strftime('%Y-%m-%d %H:%M')
                ])

        return response

    @admin.action(description='Send update notification to attendees')
    def send_update_notification(self, request, queryset):
        """Send update notification to all attendees of selected events."""
        count = 0
        for event in queryset:
            changes = {'message': 'Event details have been updated by the administrator.'}
            send_event_update_notification.delay(event.id, changes)
            count += 1

        self.message_user(
            request,
            f'Update notifications queued for {count} event(s).'
        )

    @admin.action(description='Publish selected events')
    def publish_events(self, request, queryset):
        """Publish selected events."""
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} event(s) published successfully.')

    @admin.action(description='Unpublish selected events')
    def unpublish_events(self, request, queryset):
        """Unpublish selected events."""
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} event(s) unpublished successfully.')

    @admin.action(description='Duplicate selected events')
    def duplicate_events(self, request, queryset):
        """Duplicate selected events."""
        count = 0
        for event in queryset:
            event.pk = None
            event.title = f'{event.title} (Copy)'
            event.date = timezone.now() + timezone.timedelta(days=30)
            event.save()
            count += 1

        self.message_user(request, f'{count} event(s) duplicated successfully.')


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    """
    Admin interface for EventRegistration model.
    """
    list_display = [
        'event_link', 'user_link', 'colored_status',
        'registered_at', 'event_date'
    ]
    list_filter = [
        'status',
        ('registered_at', admin.DateFieldListFilter),
        ('event__date', admin.DateFieldListFilter),
        'event__category'
    ]
    search_fields = [
        'event__title', 'user__email',
        'user__first_name', 'user__last_name'
    ]
    readonly_fields = ['registered_at']
    date_hierarchy = 'registered_at'
    actions = [
        'confirm_registrations',
        'waitlist_registrations',
        'cancel_registrations',
        'export_registrations_csv'
    ]

    fieldsets = (
        ('Registration Info', {
            'fields': ('event', 'user', 'status')
        }),
        ('Additional Info', {
            'fields': ('notes', 'registered_at')
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related.
        """
        qs = super().get_queryset(request)
        return qs.select_related('event', 'user')

    @admin.display(description='Event', ordering='event__title')
    def event_link(self, obj):
        """Display event as link."""
        url = reverse('admin:events_event_change', args=[obj.event.id])
        return format_html('<a href="{}">{}</a>', url, obj.event.title)

    @admin.display(description='User', ordering='user__email')
    def user_link(self, obj):
        """Display user as link."""
        return format_html(
            '<a href="{}">{}</a> ({})',
            reverse('admin:users_user_change', args=[obj.user.id]),
            obj.user.full_name,
            obj.user.email
        )

    @admin.display(description='Status', ordering='status')
    def colored_status(self, obj):
        """Display colored status badge."""
        colors = {
            'confirmed': 'green',
            'pending': 'orange',
            'waitlist': 'blue',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description='Event Date', ordering='event__date')
    def event_date(self, obj):
        """Display event date."""
        return obj.event.date.strftime('%Y-%m-%d %H:%M')

    @admin.action(description='Confirm selected registrations')
    def confirm_registrations(self, request, queryset):
        """Confirm selected registrations."""
        updated = queryset.update(status=EventRegistration.StatusChoices.CONFIRMED)
        self.message_user(request, f'{updated} registration(s) confirmed.')

    @admin.action(description='Move to waitlist')
    def waitlist_registrations(self, request, queryset):
        """Move selected registrations to waitlist."""
        updated = queryset.update(status=EventRegistration.StatusChoices.WAITLIST)
        self.message_user(request, f'{updated} registration(s) moved to waitlist.')

    @admin.action(description='Cancel selected registrations')
    def cancel_registrations(self, request, queryset):
        """Cancel selected registrations."""
        updated = queryset.update(status=EventRegistration.StatusChoices.CANCELLED)
        self.message_user(request, f'{updated} registration(s) cancelled.')

    @admin.action(description='Export registrations to CSV')
    def export_registrations_csv(self, request, queryset):
        """Export selected registrations to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="registrations.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Event', 'Event Date', 'User Name', 'User Email',
            'Status', 'Registered At', 'Notes'
        ])

        for reg in queryset.select_related('event', 'user'):
            writer.writerow([
                reg.event.title,
                reg.event.date.strftime('%Y-%m-%d %H:%M'),
                reg.user.full_name,
                reg.user.email,
                reg.get_status_display(),
                reg.registered_at.strftime('%Y-%m-%d %H:%M'),
                reg.notes or ''
            ])

        return response
