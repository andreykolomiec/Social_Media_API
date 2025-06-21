from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from interactions.models import Follow
from interactions.serializers import FollowSerializer, SimpleUserSerializer
from users.permissions import IsOwnerOrReadOnly


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        """Only the person who created the subscription link can delete it"""
        if self.action in ["destroy"]:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """When creating a subscription, ‘follower’ is automatically set to the current user."""
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """Restricts all subscription links to administrators only."""
        if self.request.user.is_staff and self.request.user.is_superuser:
            return Follow.objects.all().select_related("follower", "following")

        if self.action == "list":
            return Follow.objects.none()

        return super().get_queryset()

    @action(detail=Follow, methods=["get"], permission_classes=[IsAuthenticated])
    def following(self, request):
        """Gets a list of users that the current user is following.
        Get users who are subscribed to.
        Endpoint: /api/interactions/follows/following/"""

        followed_users_qs = User.objects.filter(followers_set__follower=request.user)
        serializer = SimpleUserSerializer(followed_users_qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def followers(self, request):
        """Gets a list of users who are following the current user. Get followers.
        Endpoint: /api/interactions/follows/followers/"""

        followers_of_users_qs = User.objects.filter(
            following_set__following=request.user
        )
        serializer = SimpleUserSerializer(followers_of_users_qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk=None):
        """Unsubscribe from a user by their ID (pk in the URL).
        F       or example: POST /api/interactions/follows/5/unfollow/"""

        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )
        follow_instance = Follow.objects.filter(
            follower=request.user, following=target_user
        )
        if follow_instance:
            follow_instance.delete()
            return Response(
                {"message": f"Successfully unfollowed {target_user.username}"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(
                {"detail": "You are not following this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
