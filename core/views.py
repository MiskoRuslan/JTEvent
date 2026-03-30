"""
Core app views.
"""
import os
from django.shortcuts import render
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=['Health Check'],
    description='Health check endpoint to verify API is running',
    responses={200: {'description': 'API is healthy'}}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint.
    """
    return Response(
        {
            'status': 'healthy',
            'message': 'Event Management API is running'
        },
        status=status.HTTP_200_OK
    )


# Frontend Template Views
def index(request):
    """Homepage view."""
    return render(request, 'index.html')


def events_list(request):
    """Events listing page."""
    return render(request, 'events/list.html')


def event_detail(request, event_id):
    """Event detail page."""
    return render(request, 'events/detail.html', {'event_id': event_id})


def event_create(request):
    """Event creation page."""
    return render(request, 'events/create.html')


def event_edit(request, event_id):
    """Event edit page."""
    return render(request, 'events/edit.html', {'event_id': event_id})


def login(request):
    """Login page."""
    context = {
        'GOOGLE_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID', '')
    }
    return render(request, 'auth/login.html', context)


def register(request):
    """Registration page."""
    return render(request, 'auth/register.html')


def dashboard(request):
    """User dashboard."""
    return render(request, 'profile/dashboard.html')


def profile(request):
    """User profile page."""
    return render(request, 'profile/profile.html')
