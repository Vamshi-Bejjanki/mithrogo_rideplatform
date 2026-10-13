from django.contrib import admin

from core.admin import AuditedModelAdmin, run_action
from apps.users.models import User


@admin.register(User)
class UserAdmin(AuditedModelAdmin):
    list_display = ("phone", "full_name", "role", "is_active", "is_verified", "created_at")
    list_filter = ("role", "is_active", "is_verified", "is_staff")
    search_fields = ("phone", "email", "first_name", "last_name")
    readonly_fields = ("id", "last_login", "created_at", "updated_at")
    fields = (
        "id",
        "phone",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_verified",
        "is_staff",
        "is_superuser",
        "last_login",
        "created_at",
        "updated_at",
    )
    actions = ["suspend_users", "reactivate_users"]

    @admin.action(description="Suspend selected users")
    def suspend_users(self, request, queryset):
        def handler(user, actor):
            user.is_active = False
            user.save(update_fields=["is_active", "updated_at"])

        run_action(self, request, queryset, "suspend_user", handler, "Suspended {count} user(s).")

    @admin.action(description="Reactivate selected users")
    def reactivate_users(self, request, queryset):
        def handler(user, actor):
            user.is_active = True
            user.save(update_fields=["is_active", "updated_at"])

        run_action(self, request, queryset, "reactivate_user", handler, "Reactivated {count} user(s).")
