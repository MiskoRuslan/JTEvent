"""
Celery tasks for the core app.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_email_task(subject, message, recipient_list):
    """
    Send an email asynchronously using Celery.

    Args:
        subject (str): Email subject
        message (str): Email body
        recipient_list (list): List of recipient email addresses

    Returns:
        int: Number of emails sent
    """
    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )


@shared_task
def debug_task():
    """
    Debug task for testing Celery.
    """
    return 'Celery is working!'
