from django.contrib import admin, messages

from core import audit
from core.exceptions import DomainError
from core.models import AuditLog, PlatformConfig


class AuditedModelAdmin(admin.ModelAdmin):
    """Records every admin create/update/delete in AuditLog (who, what, before/after)."""

    def save_model(self, request, obj, form, change):
        changes = {}
        if change:
            changes = {
                field: [str(form.initial.get(field)), str(form.cleaned_data.get(field))]
                for field in form.changed_data
            }
        super().save_model(request, obj, form, change)
        audit.record(request.user, "admin.update" if change else "admin.create", obj, changes)

    def delete_model(self, request, obj):
        audit.record(request.user, "admin.delete", obj)
        super().delete_model(request, obj)


def run_action(modeladmin, request, queryset, action, handler, success_text):
    """Apply handler(obj, actor) to each row, audit each success, and report the outcome."""
    done, skipped = 0, []
    for obj in queryset:
        try:
            handler(obj, request.user)
        except DomainError as exc:
            skipped.append(f"{obj}: {exc.detail}")
            continue
        audit.record(request.user, f"admin.{action}", obj)
        done += 1
    if done:
        modeladmin.message_user(request, success_text.format(count=done), messages.SUCCESS)
    for line in skipped:
        modeladmin.message_user(request, line, messages.WARNING)


@admin.register(PlatformConfig)
class PlatformConfigAdmin(AuditedModelAdmin):
    fields = (
        "search_radius_km",
        "offer_timeout_seconds",
        "max_offer_attempts",
        "location_freshness_seconds",
        "road_distance_factor",
        "average_speed_kmph",
        "min_trip_km",
        "unpaid_dues_limit",
        "service_timezone",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        config = PlatformConfig.load()
        return self.changeform_view(request, str(config.pk), "", extra_context)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "model", "object_id")
    list_filter = ("action", "model")
    search_fields = ("object_id", "actor__phone")
    readonly_fields = ("actor", "action", "model", "object_id", "changes", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
