from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):

    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        db_table = "auth_user"


class UserProfile(models.Model):
    """
    Model for storing additional information about the user profile.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", null=True, blank=True
    )
    following = models.ManyToManyField(
        "self", symmetrical=False, related_name="followers", blank=True
    )

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f"{self.user.username} Profile"

    @receiver(post_save, sender=User)
    def create_or_user_profile(sender, instance, created, **kwargs):
        """
        Signal that automatically creates or updates UserProfile
        when the User object is saved.
        """
        if created:
            UserProfile.objects.create(user=instance)

        instance.profile.save()
