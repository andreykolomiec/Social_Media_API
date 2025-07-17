from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import UserProfile
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from users.permissions import IsOwnerOrReadOnly
from rest_framework_simplejwt.views import TokenObtainPairView as JWTTokenObtainPairView
from users.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
    UserUpdateSerializer,
)


User = get_user_model()


class CreateUserView(generics.CreateAPIView):
    """
    API View for user registration (creating a new user).
    Allows any user to register with email and password.
    Returns JWT tokens upon successful registration.
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "The user has been successfully registered.",
                "user_id": user.id,
                "email": user.email,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginUserView(JWTTokenObtainPairView):
    """
    API View for user login and obtaining JWT authentication tokens.
    Uses email and password for authentication.
    """

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (AllowAny,)


class LogoutView(APIView):
    """
    Requires authentication. Blacklists the refresh token (if provided)
    to invalidate it.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {
                    "detail": f"Error during logout {e}. Ensure a valid refresh_token is provided."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class ManageUserView(generics.RetrieveUpdateAPIView):
    """
    API View for an authenticated user to retrieve and update their own User model details.
    This manages fields like email, password, first_name, last_name, etc.
    """

    serializer_class = UserUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """Retrieve and return the authenticated user's User model object."""
        return self.request.user

    @extend_schema(
        description="Retrieve or update the authenticated user's details.",
        summary="Manage current user (retrieve/update)",
        tags=["User Management"],
        request=UserUpdateSerializer,
        responses={
            200: UserRegistrationSerializer,
            401: {"description": "Unauthorized"},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update current user's details",
        request=UserRegistrationSerializer,
        responses={
            200: UserRegistrationSerializer,
            400: {"description": "Bad Request"},
            401: {"description": "Unauthorized"},
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Update current user's details",
        request=UserUpdateSerializer(partial=True),
        responses={
            200: UserUpdateSerializer,
            400: {"description": "Bad Request"},
            401: {"description": "Unauthorized"},
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


@extend_schema(
    description="API endpoint for managing user profiles.",
    summary="User Profile Management",
    tags=["User Management"],
)
class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations with user profiles.
    Allows viewing all profiles, as well as updating/deleting only your own profile.
    """

    queryset = UserProfile.objects.all().select_related("user")
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        Allows users to view their profile,
        as well as the profiles of other users.
        """
        if self.request.user.is_staff and self.request.user.is_superuser:
            return super().get_queryset()

        if self.action == "list":
            return UserProfile.objects.filter(user=self.request.user).select_related(
                "user"
            )
        return super().get_queryset()

    def get_object(self):
        """Search by user__username or pk."""
        lookup_value = self.kwargs.get("pk")

        if not lookup_value:
            raise Http404("Lookup value not provided in URL.")

        try:
            if lookup_value.isdigit():
                obj = get_object_or_404(UserProfile, pk=lookup_value)
            else:
                obj = get_object_or_404(UserProfile, user__username=lookup_value)

        except UserProfile.DoesNotExist:
            raise Http404("User profile not found.")

        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        description="Retrieve a single user profile by ID or username.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="The ID or username of the user profile.",
            )
        ],
        examples=[
            OpenApiExample(
                "Retrieve by ID",
                value="/api/users/profile/1/",
                description="Retrieve user profile with ID 1.",
                request_only=True,
            ),
            OpenApiExample(
                "Retrieve by username",
                value="/api/users/profile/john_doe/",
                description='Retrieve user profile with username "john_doe".',
                request_only=True,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a user profile (Forbidden)",
        description="Deleting a user profile via this API endpoint is forbidden.",
        responses={
            200: None,
            405: {
                "description": "Method Not Allowed - Deletion of user profiles is not allowed via this API endpoint."
            },
        },
        deprecated=True,
    )
    def destroy(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Deletion of user profiles is not allowed via this API endpoint."
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
