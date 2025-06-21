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
from users.permissions import IsOwnerOrReadOnly


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
        return UserProfile.objects.filter(user=self.request.user).select_related("user")

    def get_object(self):
        """Search by user__username or pk."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(self.queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def destroy(self, request, *args, **kwargs):
        """
        We prohibit the deletion of profiles via the API.
        Deleting a user must be a separate administrative function,
        or through deactivation, not deletion of the profile.
        """
        return Response(
            {
                "detail": "Deletion of user profiles is not allowed via this API endpoint."
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
