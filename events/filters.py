import django_filters
from django.db.models import Q
from .models import Event


class EventFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name='category', lookup_expr='iexact')
    date_from = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    location = django_filters.CharFilter(field_name='location', lookup_expr='icontains')
    organizer = django_filters.NumberFilter(field_name='organizer__id')
    is_published = django_filters.BooleanFilter(field_name='is_published')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Event
        fields = ['category', 'is_published', 'organizer']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(location__icontains=value) |
            Q(tags__icontains=value)
        )
