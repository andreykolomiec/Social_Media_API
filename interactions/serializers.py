from rest_framework import serializers
from rest_framework.authtoken.admin import User

from interactions.models import Follow


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

        if target_following != current_follower:
            raise serializers.ValidationError(
                {"following": "User to follow must be provided."}
            )

        if current_follower == target_following:
            raise serializers.ValidationError("You cannot follow yourself.")
