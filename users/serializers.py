from rest_framework import serializers
from django.contrib.auth.models import User
from users.models import UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):

    password2 = serializers.CharField(
        style={"input_type": "password"}, write_only=True, label="Password confirmation"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        """
        Checks if the passwords match and if the email is unique.
        """
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords don't match")

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        return data

    def create(self, validated_data):
        """
        Creates a new user with verified data.
        """
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    Allows you to display and update your biography and profile photo.
    """

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = UserProfile
        fields = ["id", "username", "bio", "profile_picture", "following"]
        read_only_fields = ["following"]

    def to_representation(self, instance):
        """
        We override to display only the IDs of users
        """
        representation = super().to_representation(instance)
        following_users = [
            profile.user.username for profile in instance.following.all()
        ]
        representation["following_users"] = following_users
        return representation
