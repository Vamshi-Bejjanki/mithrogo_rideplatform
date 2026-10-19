from django.contrib import admin

from apps.notifications.models import DeviceToken, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "type", "title", "is_read")
    list_filter = ("type", "is_read")
    search_fields = ("user__phone", "title")
    readonly_fields = ("user", "type", "title", "message", "data", "created_at")


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "app_version", "last_seen_at")
    list_filter = ("platform",)
    search_fields = ("user__phone", "token")
    readonly_fields = ("user", "token", "platform", "app_version", "created_at", "last_seen_at")

    def has_add_permission(self, request):
        return False
