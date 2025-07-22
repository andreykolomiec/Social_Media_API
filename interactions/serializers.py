from rest_framework import serializers
from django.contrib.auth import get_user_model

from interactions.models import Follow, Like, Comment


User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class FollowSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(
        source="follower.username", read_only=True
    )
    following_username = serializers.CharField(
        source="following.username", read_only=True
    )

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower",
            "following",
            "following_at",
            "follower_username",
            "following_username",
        ]
        read_only_fields = ["follower_username", "following_username"]

    def validate(self, data):
        """Checks that the user is not trying to subscribe to themselves"""
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request context is missing.")
        current_follower = request.user
        target_following = data.get("following")

        if current_follower == target_following:
            raise serializers.ValidationError("You cannot follow yourself.")


class LikeSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    post_content = serializers.CharField(source="post.content", read_only=True)

    class Meta:
        model = Like
        fields = [
            "id",
            "user",
            "user_username",
            "post",
            "post_content",
            "like_at",
        ]
        read_only_fields = ["user", "like_at"]


class CommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    post_content = serializers.CharField(source="post.content", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "user_username",
            "post",
            "post_content",
            "content",
            "comment_at",
        ]
        read_only_fields = ["user", "user_username", "post_content", "comment_at"]
        extra_kwargs = {
            "post": {"write_only": True},
        }
