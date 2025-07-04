from django.contrib.auth.models import User
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from interactions.models import Follow, Like, Comment
from posts.models import Post
from interactions.serializers import (
    FollowSerializer,
    SimpleUserSerializer,
    LikeSerializer,
    CommentSerializer,
)
from users.permissions import IsOwnerOrReadOnly


@extend_schema(
    description="API endpoint for managing user follow relationships.",
    summary="User Follow Management",
    tags=["Interactions - Follows"],
)
class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        """Only the person who created the subscription link can delete it"""
        if self.action in ["destroy"]:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Create a new follow relationship",
        description="Allow an authenticated user to follow another user. The 'follower' is automatically set to the current user.",
        request=FollowSerializer,
        responses={
            201: FollowSerializer,
            400: {
                "description": "Invalid data (e.g., trying to follow yourself, or already following)."
            },
            401: {"description": "Authentication credentials were not provided."},
        },
        examples=[
            OpenApiExample(
                "Follow User with ID 5",
                value={"following": 5},  # Приклад тіла запиту
                request_only=True,
                media_type="application/json",
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        """Overrides the default create method to add OpenAPI documentation."""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        When creating a subscription, 'follower' is automatically set to the current user.
        """
        serializer.save(follower=self.request.user)

    def get_queryset(self):
        """Restricts all subscription links to administrators only.
        Administrators (staff and superuser) can see all follow relationships.
        For detail actions (retrieve, destroy), the specific object is fetched by its ID.
        """

        if self.request.user.is_staff and self.request.user.is_superuser:
            return Follow.objects.all().select_related("follower", "following")

        if self.action == "list":
            return Follow.objects.none()

        return super().get_queryset()

    @extend_schema(
        summary="Get users followed by the current user",
        description="Retrieve a list of users that the authenticated user is currently following.",
        responses={
            200: SimpleUserSerializer(many=True),
            401: {"description": "Authentication credentials were not provided."},
        },
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def following(self, request):
        """Gets a list of users that the current user is following.
        Get users who are subscribed to.
        Endpoint: /api/interactions/follows/following/"""

        followed_users_qs = User.objects.filter(followers_set__follower=request.user)
        serializer = SimpleUserSerializer(followed_users_qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get users who follow the current user",
        description="Retrieve a list of users who are currently following the authenticated user.",
        responses={
            200: SimpleUserSerializer(many=True),
            401: {"description": "Authentication credentials were not provided."},
        },
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def followers(self, request):
        """Gets a list of users who are following the current user. Get followers.
        Endpoint: /api/interactions/follows/followers/"""

        followers_of_users_qs = User.objects.filter(
            following_set__following=request.user
        )
        serializer = SimpleUserSerializer(followers_of_users_qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Unfollow a user by their ID",
        description="Allow an authenticated user to unfollow another user by providing the target user's ID."
        " This action finds and deletes the specific follow relationship.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="The ID of the user to unfollow.",
            )
        ],
        responses={
            204: {"description": "Successfully unfollowed."},
            400: {"description": "You are not following this user."},
            401: {"description": "Authentication credentials were not provided."},
            404: {"description": "User not found."},
        },
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
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
        ).first()
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


@extend_schema(
    description="API endpoint for managing likes on posts.",
    summary="Like Management",
    tags=["Interactions - Likes"],
)
class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all().select_related("user", "post")
    serializer_class = LikeSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List likes with optional filters",
        description="Retrieves a list of likes. Can be filtered by `post_id` to show likes for a specific post,"
        " or `my_like=true` to show only likes made by the current authenticated user.",
        parameters=[
            OpenApiParameter(
                name="post_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter likes by a specific post ID.",
                required=False,
                examples=[
                    OpenApiExample(
                        "Likes for Post 10", value="10", media_type="text/plain"
                    ),
                ],
            ),
            OpenApiParameter(
                name="my_like",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="If 'true', only show likes made by the current authenticated user.",
                required=False,
                examples=[
                    OpenApiExample(
                        "My own likes", value="true", media_type="text/plain"
                    ),
                ],
            ),
        ],
        responses={
            200: LikeSerializer(many=True),
            401: {"description": "Authentication credentials were not provided."},
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        post_id = self.request.query_params.get("post_id")
        if post_id:
            try:
                int(post_id)
                queryset = queryset.filter(post__id=post_id)

            except ValueError:
                raise ValidationError({"post_id": "Must be a valid integer"})

        my_like = self.request.query_params.get("my_like")
        if my_like == "true":
            queryset = queryset.filter(user=self.request.user)

        return queryset

    @extend_schema(
        summary="Retrieve a single like",
        description="Retrieves details of a specific like by its ID. Any authenticated user can retrieve it.",
        responses={
            200: LikeSerializer,
            401: {"description": "Authentication credentials were not provided."},
            404: {"description": "Like not found."},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new like for a post",
        description="Allows an authenticated user to like a post. A user can only like a post once."
        " The 'user' field is automatically set to the current authenticated user.",
        request=LikeSerializer,
        responses={
            201: LikeSerializer,
            400: {"description": "Invalid data ( you have already liked this post)."},
            401: {"description": "Authentication credentials were not provided."},
        },
        examples=[
            OpenApiExample(
                "Like Post with ID 10",
                value={"post": 10},
                request_only=True,
                media_type="application/json",
            ),
            OpenApiExample(
                "Like Post with ID 5",
                value={"post": 5},
                request_only=True,
                media_type="application/json",
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        post_id = request.data.get("post")
        if not post_id:
            return Response(
                {"detail": "Post ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExists:
            return Response(
                {"detail": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if Like.objects.filter(user=request.user, post=post).exists():
            return Response(
                {"detail": "You have already liked this post."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data={"post": post_id})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Unlike a post",
        description="Allows the user who liked a post to remove their like by providing the like's ID."
        " This operation effectively 'unlikes' the post.",
        responses={
            204: {"description": "Like successfully removed."},
            401: {"description": "Authentication credentials were not provided."},
            403: {
                "description": "Permission denied (not the user who liked this specific like)."
            },
            404: {"description": "Like not found."},
        },
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    description="API endpoint for managing comments on post. Allows authenticated users to create, retrieve, update, and delete comments. ",
    summary="Comment Management",
    tags=["Interactions - Comments"],
)
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().select_related("user", "post")
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        """
        Set permissions for different actions.
        Only authenticated users can list, retrieve, create comments.
        Only the author of the comment can update or delete it.
        """
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List comments with optional filters",
        description="Retrieves a list of comments. Can be filtered by `post_id` to show comments for a specific post,"
        " or `my_comments=true` to show only comments made by the current authenticated user.",
        parameters=[
            OpenApiParameter(
                name="post_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter comments by a specific post ID.",
                required=False,
                examples=[
                    OpenApiExample(
                        "Comments for Post 10", value="10", media_type="text/plain"
                    ),
                ],
            ),
            OpenApiParameter(
                name="my_comments",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="If 'true', only show comments made by the current authenticated user.",
                required=False,
                examples=[
                    OpenApiExample(
                        "My own comments", value="true", media_type="text/plain"
                    ),
                ],
            ),
        ],
        responses={
            200: CommentSerializer(many=True),
            401: {"description": "Authentication credentials were not provided."},
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        post_id = self.request.query_params.get("post_id")
        if post_id:
            try:
                int(post_id)
                queryset = queryset.filter(post__id=post_id)

            except ValueError:
                raise ValidationError({"post_id": "Mast by a valid integer"})

        my_comments = self.request.query_params.get("my_like")
        if my_comments == "true":
            queryset = queryset.filter(user=self.request.user)

        return queryset

    @extend_schema(
        summary="Retrieve a single comment",
        description="Retrieves details of a specific like by its ID. Any authenticated user can retrieve it.",
        responses={
            200: CommentSerializer,
            401: {"description": "Authentication credentials were not provided."},
            404: {"description": "Comment not found."},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new comment for a post",
        description="Allows an authenticated user to add comment a post."
        " The 'user' field is automatically set to the current authenticated user.",
        request=CommentSerializer,
        responses={
            201: CommentSerializer,
            400: {
                "description": "Invalid data ( post does not exist, or content is empty)."
            },
            401: {"description": "Authentication credentials were not provided."},
            404: {"description": "Post not found."},
        },
        examples=[
            OpenApiExample(
                "Comment on Post with ID 10",
                value={"post": 10, "comment": "This is a great post!"},
                request_only=True,
                media_type="application/json",
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        post_id = request.data.get("post")
        content = request.data.get("content")
        if not post_id:
            raise ValidationError({"post": "Post ID is required."})
        if not content:
            raise ValidationError({"content": "Comment content cannot be empty."})

        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExists:
            return Response(
                {"detail": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if Comment.objects.filter(user=request.user, post=post).exists():
            return Response(
                {"detail": "You have already commented on this post."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data={"post": post_id, "content": content})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Update a comment",
        description="Allows the author of the comment to fully update (PUT) or partially update (PATCH) their comment.",
        request=CommentSerializer,
        responses={
            200: CommentSerializer,
            400: {"description": "Invalid data provided."},
            401: {"description": "Authentication credentials were not provided."},
            403: {"description": "Permission denied (not the author)."},
            404: {"description": "Comment not found."},
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a comment",
        description="Allows the author of the comment to delete their comment.",
        responses={
            204: {"description": "Comment successfully deleted."},
            401: {"description": "Authentication credentials were not provided."},
            403: {"description": "Permission denied (not the author)."},
            404: {"description": "Comment not found."},
        },
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
