"""
Serializers for Event and EventRegistration models.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Event, EventRegistration
from users.serializers import UserSerializer


class EventRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for EventRegistration model.
    """
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    event_title = serializers.CharField(source='event.title', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'event_title', 'user', 'user_id',
            'registered_at', 'status', 'notes'
        ]
        read_only_fields = ['id', 'registered_at']

    def validate(self, attrs):
        """
        Validate registration.
        """
        event = attrs.get('event')
        user = self.context['request'].user

        # Check if event is in the past
        if event.is_past:
            raise serializers.ValidationError('Cannot register for past events.')

        # Check if user is already registered
        if EventRegistration.objects.filter(
            event=event,
            user=user,
            status__in=[EventRegistration.StatusChoices.CONFIRMED, EventRegistration.StatusChoices.WAITLIST]
        ).exists():
            raise serializers.ValidationError('You are already registered for this event.')

        return attrs


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for Event model with read operations.
    """
    organizer = UserSerializer(read_only=True)
    organizer_id = serializers.IntegerField(write_only=True, required=False)
    attendees_count = serializers.IntegerField(read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    tags_list = serializers.ListField(
        source='get_tags_list',
        read_only=True,
        help_text='List of tags'
    )
    cover_image_url = serializers.CharField(
        source='get_cover_image_url',
        read_only=True,
        help_text='Cover image URL or default banner'
    )
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'date', 'location',
            'organizer', 'organizer_id', 'category', 'max_attendees',
            'cover_image', 'cover_image_url', 'tags', 'tags_list', 'is_published',
            'created_at', 'updated_at', 'attendees_count',
            'available_spots', 'is_full', 'is_past', 'is_upcoming',
            'is_registered'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_registered(self, obj):
        """
        Check if the current user is registered for this event.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return EventRegistration.objects.filter(
                event=obj,
                user=request.user,
                status__in=[EventRegistration.StatusChoices.CONFIRMED, EventRegistration.StatusChoices.WAITLIST]
            ).exists()
        return False

    def validate_date(self, value):
        """
        Validate that event date is in the future.
        """
        # Make sure we're comparing timezone-aware datetimes
        now = timezone.now()

        # If value is naive, make it aware
        if timezone.is_naive(value):
            value = timezone.make_aware(value)

        if value < now:
            raise serializers.ValidationError('Event date must be in the future.')

        return value

    def validate_max_attendees(self, value):
        """
        Validate max_attendees is positive.
        """
        if value is not None and value < 1:
            raise serializers.ValidationError('Maximum attendees must be at least 1.')
        return value


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Event creation and updates.
    """
    tags_list = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
        help_text='List of tags'
    )

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'date', 'location',
            'category', 'max_attendees', 'cover_image',
            'tags', 'tags_list', 'is_published'
        ]
        read_only_fields = ['id']

    def validate_date(self, value):
        """
        Validate that event date is in the future.
        """
        # Make sure we're comparing timezone-aware datetimes
        now = timezone.now()

        # If value is naive, make it aware
        if timezone.is_naive(value):
            value = timezone.make_aware(value)

        if value < now:
            raise serializers.ValidationError('Event date must be in the future.')

        return value

    def validate_max_attendees(self, value):
        """
        Validate max_attendees is positive.
        """
        if value is not None and value < 1:
            raise serializers.ValidationError('Maximum attendees must be at least 1.')
        return value

    def create(self, validated_data):
        """
        Create event with tags handling.
        """
        tags_list = validated_data.pop('tags_list', None)
        if tags_list:
            validated_data['tags'] = ', '.join(tags_list)

        # Set organizer from request
        validated_data['organizer'] = self.context['request'].user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update event with tags handling.
        """
        tags_list = validated_data.pop('tags_list', None)
        if tags_list:
            validated_data['tags'] = ', '.join(tags_list)

        return super().update(instance, validated_data)


class EventListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for event lists.
    """
    organizer_name = serializers.CharField(source='organizer.get_full_name', read_only=True)
    attendees_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    cover_image_url = serializers.CharField(
        source='get_cover_image_url',
        read_only=True,
        help_text='Cover image URL or default banner'
    )

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'date', 'location', 'category',
            'cover_image', 'cover_image_url', 'organizer_name', 'attendees_count',
            'max_attendees', 'is_full', 'is_past', 'is_published'
        ]


class EventRegistrationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing event registrations.
    """
    event = EventListSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventRegistration
        fields = ['id', 'event', 'user', 'registered_at', 'status', 'notes']
        read_only_fields = ['id', 'registered_at']
