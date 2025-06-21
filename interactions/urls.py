from django.urls import path, include
from interactions.views import FollowViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("follows", FollowViewSet)
urlpatterns = [path("", include(router.urls))]

app_name = "interactions"
