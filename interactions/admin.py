from django.contrib import admin
from interactions.models import Comment, Like, Follow


admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Follow)
