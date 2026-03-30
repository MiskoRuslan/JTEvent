"""
Core app URL configuration.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('health/', views.health_check, name='health-check'),

    # Frontend routes
    path('', views.index, name='index'),
    path('events/', views.events_list, name='events-list'),
    path('events/<int:event_id>/', views.event_detail, name='event-detail'),
    path('events/create/', views.event_create, name='event-create'),
    path('events/<int:event_id>/edit/', views.event_edit, name='event-edit'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
]
