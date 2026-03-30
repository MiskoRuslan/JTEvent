from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Event, EventRegistration
from .serializers import (
    EventSerializer,
    EventCreateUpdateSerializer,
    EventListSerializer,
    EventRegistrationSerializer,
    EventRegistrationListSerializer
)
from .filters import EventFilter
from .permissions import IsOrganizerOrReadOnly, IsAuthenticatedOrReadOnly
from users.serializers import UserSerializer


@extend_schema_view(
    list=extend_schema(tags=['Events'], summary='List all events'),
    retrieve=extend_schema(tags=['Events'], summary='Get event details'),
    create=extend_schema(tags=['Events'], summary='Create new event'),
    update=extend_schema(tags=['Events'], summary='Update event'),
    partial_update=extend_schema(tags=['Events'], summary='Partially update event'),
    destroy=extend_schema(tags=['Events'], summary='Delete event'),
)
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().select_related('organizer').order_by('-date')
    permission_classes = [IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'description', 'location', 'tags']
    ordering_fields = ['date', 'created_at', 'title']
    ordering = ['-date']

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        return EventSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if self.action == 'list':
            if not user.is_authenticated or not user.is_staff:
                queryset = queryset.filter(is_published=True)

        return queryset

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @extend_schema(
        tags=['Events'],
        summary='Register for event',
        request=None,
        responses={201: EventRegistrationSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request, pk=None):
        event = self.get_object()
        user = request.user

        # Check if user already has an active registration
        existing_registration = EventRegistration.objects.filter(
            event=event,
            user=user
        ).first()

        if existing_registration and existing_registration.status in [
            EventRegistration.StatusChoices.CONFIRMED,
            EventRegistration.StatusChoices.WAITLIST
        ]:
            return Response(
                {'error': 'You are already registered for this event.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if event.is_past:
            return Response(
                {'error': 'Cannot register for past events.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        registration_status = EventRegistration.StatusChoices.CONFIRMED
        if event.is_full:
            registration_status = EventRegistration.StatusChoices.WAITLIST

        # If there's a cancelled registration, update it instead of creating new
        if existing_registration and existing_registration.status == EventRegistration.StatusChoices.CANCELLED:
            existing_registration.status = registration_status
            existing_registration.save()
            registration = existing_registration
        else:
            registration = EventRegistration.objects.create(
                event=event,
                user=user,
                status=registration_status
            )

        # Send confirmation email asynchronously
        from .tasks import send_registration_confirmation
        send_registration_confirmation.delay(user.id, event.id)

        serializer = EventRegistrationSerializer(registration, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Events'],
        summary='Unregister from event',
        request=None,
        responses={204: None}
    )
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unregister(self, request, pk=None):
        event = self.get_object()
        user = request.user

        try:
            registration = EventRegistration.objects.get(
                event=event,
                user=user,
                status__in=[EventRegistration.StatusChoices.CONFIRMED, EventRegistration.StatusChoices.WAITLIST]
            )
            registration.status = EventRegistration.StatusChoices.CANCELLED
            registration.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except EventRegistration.DoesNotExist:
            return Response(
                {'error': 'You are not registered for this event.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        tags=['Events'],
        summary='List event attendees',
        responses={200: UserSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        event = self.get_object()

        if not (request.user == event.organizer or request.user.is_staff):
            return Response(
                {'error': 'Only the organizer can view attendees.'},
                status=status.HTTP_403_FORBIDDEN
            )

        registrations = EventRegistration.objects.filter(
            event=event,
            status=EventRegistration.StatusChoices.CONFIRMED
        ).select_related('user')

        users = [reg.user for reg in registrations]
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        tags=['Events'],
        summary='List my organized events',
        responses={200: EventListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_events(self, request):
        events = Event.objects.filter(organizer=request.user).order_by('-date')
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = EventListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = EventListSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Event Registrations'], summary='List all registrations'),
    retrieve=extend_schema(tags=['Event Registrations'], summary='Get registration details'),
)
class EventRegistrationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EventRegistration.objects.all().select_related('event', 'user').order_by('-registered_at')
    serializer_class = EventRegistrationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'event']
    ordering_fields = ['registered_at']
    ordering = ['-registered_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_staff:
            queryset = queryset.filter(user=user)

        return queryset

    @extend_schema(
        tags=['Event Registrations'],
        summary='List my registrations',
        responses={200: EventRegistrationListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def my_registrations(self, request):
        registrations = EventRegistration.objects.filter(user=request.user).select_related('event').order_by('-registered_at')
        page = self.paginate_queryset(registrations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(registrations, many=True)
        return Response(serializer.data)
