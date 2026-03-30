"""
User authentication and profile management views.
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    GoogleAuthSerializer
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint.
    Creates a new user account with the provided credentials.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Authentication'],
        summary='Register a new user',
        description='Create a new user account with email, password, and profile information.',
        responses={
            201: UserSerializer,
            400: OpenApiTypes.OBJECT
        }
    )
    def post(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Registration request data: {request.data}")

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Registration validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view that includes user data.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        tags=['Authentication'],
        summary='Obtain JWT token pair',
        description='Get access and refresh tokens by providing email and password.'
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the authenticated user's profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
        tags=['User Profile'],
        summary='Get current user profile',
        description='Retrieve the authenticated user\'s profile information.'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=['User Profile'],
        summary='Update current user profile',
        description='Update the authenticated user\'s profile information.'
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        tags=['User Profile'],
        summary='Update current user profile',
        description='Update the authenticated user\'s profile information.'
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)


class ChangePasswordView(APIView):
    """
    Change password endpoint for authenticated users.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['User Profile'],
        summary='Change password',
        description='Change the password for the authenticated user.',
        request=ChangePasswordSerializer,
        responses={
            200: {'description': 'Password changed successfully'},
            400: OpenApiTypes.OBJECT
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout endpoint that blacklists the refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Authentication'],
        summary='Logout user',
        description='Logout the user by blacklisting the refresh token.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string', 'description': 'Refresh token'}
                },
                'required': ['refresh']
            }
        },
        responses={
            200: {'description': 'Logged out successfully'},
            400: OpenApiTypes.OBJECT
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'message': 'Logged out successfully.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=['User Profile'],
    summary='Get user by ID',
    description='Retrieve public profile information for a specific user.',
    responses={
        200: UserSerializer,
        404: {'description': 'User not found'}
    }
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_user_profile(request, user_id):
    """
    Get public profile of a user by ID.
    """
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=['Authentication'],
    summary='Verify email',
    description='Verify user email with a verification token.',
    parameters=[
        OpenApiParameter(
            name='token',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Email verification token'
        )
    ],
    responses={
        200: {'description': 'Email verified successfully'},
        400: {'description': 'Invalid or expired token'}
    }
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    """
    Verify user email with token (placeholder - implement with actual email service).
    """
    token = request.query_params.get('token')

    if not token:
        return Response(
            {'error': 'Verification token is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # TODO: Implement actual email verification logic
    # For now, this is a placeholder

    return Response({
        'message': 'Email verification endpoint. Implementation pending.'
    }, status=status.HTTP_200_OK)


class GoogleAuthView(APIView):
    """
    Google OAuth authentication endpoint.
    Accepts a Google ID token and returns JWT tokens.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Authentication'],
        summary='Google OAuth login',
        description='Authenticate with Google OAuth by providing a Google ID token. Returns JWT tokens.',
        request=GoogleAuthSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'user': {'type': 'object'},
                    'tokens': {
                        'type': 'object',
                        'properties': {
                            'access': {'type': 'string'},
                            'refresh': {'type': 'string'}
                        }
                    },
                    'message': {'type': 'string'}
                }
            },
            400: OpenApiTypes.OBJECT
        }
    )
    def post(self, request):
        """
        Authenticate user with Google OAuth token.
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Google OAuth request data: {request.data}")

        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        google_token = serializer.validated_data['token']
        logger.info(f"Validating Google token (length: {len(google_token)})")

        try:
            # Verify Google token and get user info
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                None  # We'll accept any audience for development
            )

            # Extract user information
            google_id = idinfo.get('sub')
            email = idinfo.get('email')
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            email_verified = idinfo.get('email_verified', False)
            picture = idinfo.get('picture', '')

            # Check if user exists
            user = None
            try:
                user = User.objects.get(google_id=google_id)
            except User.DoesNotExist:
                # Try to find by email
                try:
                    user = User.objects.get(email=email)
                    # Link Google account
                    user.google_id = google_id
                    if email_verified:
                        user.email_verified = True
                    user.save()
                except User.DoesNotExist:
                    # Create new user
                    username = email.split('@')[0]
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1

                    user = User.objects.create_user(
                        email=email,
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        google_id=google_id,
                        email_verified=email_verified
                    )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            # Return same format as CustomTokenObtainPairSerializer
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Invalid token
            logger.error(f"Invalid Google token: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Invalid Google token: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Google auth failed: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Authentication failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
