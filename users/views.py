from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from .models import UserProfile
from rest_framework import viewsets
from django.shortcuts import get_object_or_404


class UserRegistrationView(generics.CreateAPIView):
    """
    API View for registering a new user.
    Allows any user (AllowAny) to register.
    """

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                "message": "The user has been successfully registered.",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(ObtainAuthToken):
    """
    API View for user login and obtaining an authentication token.
    """

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user_id": user.id, "username": user.username},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Requires authentication. Deletes the authentication token.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"detail": f"Error during logout {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations with user profiles.
    Allows viewing all profiles, as well as updating/deleting only your own profile.
    """

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        Allows users to view their profile,
        as well as the profiles of other users.
        """
        if self.request.user.is_staff and self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.all()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieving a profile by ID or username.
        """
        lookup_value = self.kwargs.get("lookup_field")
        if lookup_value.isdigit():
            obj = get_object_or_404(UserProfile, pk=lookup_value)
        else:
            obj = get_object_or_404(User, user__username=lookup_value)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Allows the user to update only their profile.
        """
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to edit this profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Allows the user to partially update only their profile.
        """
        partial = self.get_object()
        if partial.user != request.user:
            return Response(
                {"detail": "You do not have permission to edit this profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        We prohibit the deletion of profiles via the API.
        Deleting a user must be a separate administrative function,
        or through deactivation, not deletion of the profile.
        """
        return Response(
            {"detail": "Deleting a user must be a separate administrative function."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
