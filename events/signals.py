from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Event, EventRegistration
from .tasks import send_registration_confirmation, send_event_update_notification


@receiver(post_save, sender=EventRegistration)
def event_registration_created(sender, instance, created, **kwargs):
    """Send confirmation email when user registers for an event"""
    if created and instance.status == EventRegistration.StatusChoices.CONFIRMED:
        send_registration_confirmation.delay(instance.user.id, instance.event.id)


@receiver(pre_save, sender=Event)
def track_event_changes(sender, instance, **kwargs):
    """Track changes to event before saving"""
    if instance.pk:
        try:
            old_instance = Event.objects.get(pk=instance.pk)
            instance._old_instance = old_instance
        except Event.DoesNotExist:
            pass


@receiver(post_save, sender=Event)
def event_updated(sender, instance, created, **kwargs):
    """Send update notification when event details change"""
    if not created and hasattr(instance, '_old_instance'):
        old = instance._old_instance
        changes = []

        if old.title != instance.title:
            changes.append(f"Title changed to: {instance.title}")

        if old.date != instance.date:
            changes.append(f"Date/time changed to: {instance.date.strftime('%B %d, %Y at %I:%M %p')}")

        if old.location != instance.location:
            changes.append(f"Location changed to: {instance.location}")

        if old.description != instance.description:
            changes.append("Event description has been updated")

        if changes:
            changes_text = "\n".join(f"• {change}" for change in changes)
            send_event_update_notification.delay(instance.id, changes_text)
