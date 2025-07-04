from users.models import User
from django.db import models


class Post(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts", verbose_name="Author"
    )
    content = models.TextField(verbose_name="Content")
    image = models.ImageField(
        upload_to="post_images/", verbose_name="Image", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Post created by {self.author.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
