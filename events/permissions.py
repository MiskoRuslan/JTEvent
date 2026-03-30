from rest_framework import permissions


class IsOrganizer(permissions.BasePermission):
    """
    Permission check if user is the event organizer.
    """
    def has_object_permission(self, request, view, obj):
        return obj.organizer == request.user


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Allow read access to anyone, write access only to organizer.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user or request.user.is_staff


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Allow read access to anyone, write access only to authenticated users.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
