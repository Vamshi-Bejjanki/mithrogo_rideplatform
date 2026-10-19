from rest_framework.permissions import BasePermission

from apps.users.models import Role


class IsAdminRole(BasePermission):
    """Only active ADMIN accounts. Customers and captains get 403, whatever they try."""

    message = "Only admins can use this endpoint."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.role == Role.ADMIN)
