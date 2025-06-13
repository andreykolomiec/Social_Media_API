from django.contrib.auth.models import User
from django.db import models

from posts.models import Post


class Follow(models.Model):
    """
    A model for tracking “following” relationships between users.
    """

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following_set",
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers_set",
    )
    following_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")

    def __str__(self):
        return f"{self.follower} follows {self.following}"


class Like(models.Model):
    """
    A model for tracking likes on posts.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes", verbose_name="user"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes", verbose_name="post"
    )
    like_at = models.DateTimeField(auto_now_add=True, verbose_name="date_of_like")

    class Meta:
        unique_together = ("user", "post")
        verbose_name = "like"
        verbose_name_plural = "likes"
        ordering = [
            "-like_at",
        ]

    def __str__(self):
        return f"{self.user.username} likes {self.post}"


class Comment(models.Model):
    """
    Model for storing comments on posts.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="post"
    )
    content = models.TextField(verbose_name="content")
    comment_at = models.DateTimeField(auto_now_add=True, verbose_name="date_of_comment")

    class Meta:
        unique_together = ("user", "post")
        verbose_name = "comment"
        verbose_name_plural = "comments"
        ordering = [
            "-comment_at",
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on Post {self.post}"
