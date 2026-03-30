"""
URL configuration for users app.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    UserRegistrationView,
    CustomTokenObtainPairView,
    UserProfileView,
    ChangePasswordView,
    LogoutView,
    GoogleAuthView,
    get_user_profile,
    verify_email
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token-verify'),

    # Google OAuth
    path('google/', GoogleAuthView.as_view(), name='google-auth'),

    # Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/<int:user_id>/', get_user_profile, name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Email Verification
    path('verify-email/', verify_email, name='verify-email'),
]
