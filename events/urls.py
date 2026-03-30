from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, EventRegistrationViewSet

app_name = 'events'

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'registrations', EventRegistrationViewSet, basename='registration')

urlpatterns = [
    path('', include(router.urls)),
]
