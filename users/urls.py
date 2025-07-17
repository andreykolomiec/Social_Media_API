from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import (
    CreateUserView,
    LoginUserView,
    ManageUserView,
    LogoutView,
    UserProfileViewSet,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

router = DefaultRouter()
router.register(r"profile", UserProfileViewSet, basename="profile")

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="register"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", ManageUserView.as_view(), name="me"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("", include(router.urls)),
]

app_name = "users"
