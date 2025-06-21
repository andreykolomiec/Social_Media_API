from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission that allows only the owner of the object to edit or delete it.
    Allows anyone to read."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user
