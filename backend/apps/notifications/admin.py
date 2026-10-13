from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "type", "title", "is_read")
    list_filter = ("type", "is_read")
    search_fields = ("user__phone", "title")
    readonly_fields = ("user", "type", "title", "message", "data", "created_at")
