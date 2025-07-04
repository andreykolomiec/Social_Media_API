from rest_framework import serializers
from django.contrib.auth import get_user_model

from users.models import UserProfile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration. Allows registration with email and password,
    and includes password confirmation.
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=5)
    password2 = serializers.CharField(
        style={"input_type": "password"}, write_only=True, label="Password confirmation"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate(self, data):
        """
        Checks if the passwords match and if the email is unique.
        """
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords don't match"})

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        return data

    def create(self, validated_data):
        """
        Creates a new user with verified data, using email.
        """
        validated_data.pop("password2")
        email = validated_data.get("email")
        validated_data["username"] = email
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining JWT tokens using email and password.
    It extends simplejwt's default serializer to change the username field to email.
    """

    username_field = "email"

    def validate(self, attrs):
        attrs["username"] = attrs.get(self.username_field)

        return super().validate(attrs)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    Allows you to display and update your biography and profile photo.
    Displays user's email and username, and lists followed users by their email.
    """

    email = serializers.CharField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    following = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="user__email"
    )

    class Meta:
        model = UserProfile
        fields = ["id", "username", "email", "bio", "profile_picture", "following"]
        read_only_fields = ["id", "following", "username", "email"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing user's details.
    Allows partial updates and handling of password change.
    """

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password")
        extra_kwargs = {
            "password": {
                "write_only": True,
                "min_length": 5,
                "required": False,
                "style": {"input_type": "password"},
            },
        }

    def validate_email(self, value):
        if (
            self.instance
            and self.instance.email != value
            and User.objects.filter(email=value).exists()
        ):
            raise serializers.ValidationError(
                "This email is already in use by another user."
            )
        return value

    def update(self, instance, validated_data):
        """
        Update user instance, handling password change separately.
        """
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user
