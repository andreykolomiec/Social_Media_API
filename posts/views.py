from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from posts.models import Post
from posts.serializers import PostSerializer
from posts.permissions import IsAuthorOrReadOnly
from interactions.models import Follow
from django.contrib.auth.models import User


@extend_schema(
    description="API endpoint for managing posts. Users can create, view, update, and delete their own posts.",
    summary="Post Management",
    tags=["Posts"],
)
class PostViewSet(viewsets.ModelViewSet):
    queryset = (
        Post.objects.all().select_related("author").annotate(like_count=Count("likes"))
    )
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly, IsAuthenticated]

    def perform_create(self, serializer):
        """
        When creating a post, the author is set to the current user.
        """
        serializer.save(author=self.request.user)

    @extend_schema(
        summary="List posts with optional filtering",
        description="Retrieves a list of posts."
        " Can be filtered by `my_posts=true` to show only current user's posts,"
        " or `following=true` to show posts from users the current user follows.",
        parameters=[
            OpenApiParameter(
                name="my_posts",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="If 'true', only show posts created by the current authenticated user.",
                required=False,
                examples=[
                    OpenApiExample(
                        "Filter by own posts",
                        value="true",
                        media_type="text/plain",
                    )
                ],
            ),
            OpenApiParameter(
                name="following",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="If 'true', show posts from users the current authenticated user is following. Requires user to have a 'profile' object.",
                required=False,
                examples=[
                    OpenApiExample(
                        "Filter by followed users",
                        value="true",
                        media_type="text/plain",
                    )
                ],
            ),
            OpenApiParameter(
                name="hashtag",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter posts by content containing a specific hashtag (e.g., '#django').",
                required=False,
                examples=[
                    OpenApiExample(
                        "'Filter by hashtag",
                        value="python",
                        media_type="text/plain",
                    ),
                ],
                response={
                    200: PostSerializer(many=True),
                    401: {
                        "description": "Authentication credentials were not provided."
                    },
                },
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            return queryset.none()

        """Filtering by own posts (if, for example, /posts/?my_posts=true)"""
        if self.request.query_params.get("my_posts") == "true":
            queryset = queryset.filter(author=self.request.user)
            return queryset

        """Filtering by posts of users that the current user is subscribed to"""
        if self.request.query_params.get("following") == "true":
            if hasattr(self.request.user, "profile"):
                followed_user_ids = self.request.user.profile.following.values_list(
                    "user__id", flat=True
                )
                queryset = queryset.filter(author__id__in=followed_user_ids)
            else:
                return Post.objects.none()

            return queryset

        return queryset

    @extend_schema(
        summary="Create a new post",
        description="Allows an authenticated user to create a new post.",
        request=PostSerializer,
        responses={
            200: PostSerializer,
            400: {"description": "Invalid data provided."},
            401: {"description": "Authentication credentials were not provided."},
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a post",
        description="Retrieve a single post by its ID.",
        responses={
            200: PostSerializer,
            404: {"description": "Post not found."},
            401: {"description": "Authentication credentials were not provided."},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update a post",
        description="Allows an authenticated user to update a post.",
        request=PostSerializer,
        responses={
            200: PostSerializer,
            400: {"description": "Invalid data provided."},
            401: {"description": "Authentication credentials were not provided."},
            403: {"description": "Permission denied (not the author)."},
            404: {"description": "Post not found."},
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a post",
        description="Allows the author of the post to be deleted their post.",
        responses={
            204: {"description": "Post deleted."},
            401: {"description": "Authentication credentials were not provided."},
            403: {"description": "Permission denied (not the author)."},
            404: {"description": "Post not found."},
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
