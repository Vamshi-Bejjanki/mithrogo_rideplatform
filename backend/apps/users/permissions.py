from rest_framework.permissions import BasePermission

from apps.users.models import Role


class _RolePermission(BasePermission):
    role = None
    message = None

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == self.role)


class IsCustomer(_RolePermission):
    role = Role.CUSTOMER
    message = "Only customers can use this endpoint."


class IsCaptain(_RolePermission):
    role = Role.CAPTAIN
    message = "Only captains can use this endpoint."
