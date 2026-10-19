from django.contrib import admin

from core.admin import AuditedModelAdmin, csv_export_action, run_action
from apps.subscriptions.models import CaptainSubscription, PlatformDue, RideShareDay, SubscriptionPlan
from apps.subscriptions.services import settle_due_offline as _mark_settled_offline
from apps.subscriptions.services import waive_due as _waive


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(AuditedModelAdmin):
    list_display = (
        "code",
        "name",
        "plan_type",
        "amount",
        "vehicle_type",
        "duration_hours",
        "qualifying_rides",
        "shortfall_fee",
        "is_active",
    )
    list_filter = ("plan_type", "is_active")
    search_fields = ("code", "name")


@admin.register(CaptainSubscription)
class CaptainSubscriptionAdmin(AuditedModelAdmin):
    list_display = ("captain", "plan", "status", "start_at", "expires_at", "penalty_pending")
    list_filter = ("status", "plan__plan_type", "plan")
    search_fields = ("captain__user__phone",)
    raw_id_fields = ("captain", "payment")
    readonly_fields = ("start_at", "expires_at", "penalty_pending", "created_at", "updated_at")


@admin.register(RideShareDay)
class RideShareDayAdmin(admin.ModelAdmin):
    list_display = (
        "captain",
        "service_date",
        "completed_rides",
        "qualifying_rides",
        "platform_ride",
        "status",
        "shortfall",
    )
    list_filter = ("status", "shortfall")
    search_fields = ("captain__user__phone",)
    readonly_fields = [f.name for f in RideShareDay._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PlatformDue)
class PlatformDueAdmin(AuditedModelAdmin):
    list_display = ("captain", "due_type", "amount", "status", "ride", "created_at", "settled_at")
    list_filter = ("due_type", "status")
    search_fields = ("captain__user__phone",)
    raw_id_fields = ("captain", "ride", "payment")
    actions = ["mark_settled_offline", "waive_dues", "export_csv"]
    export_csv = csv_export_action(
        [("captain", "captain__user__phone"), ("type", "due_type"), ("amount", "amount"), ("status", "status"),
         ("ride", "ride_id"), ("created_at", "created_at"), ("settled_at", "settled_at")],
        "platform-dues",
    )

    @admin.action(description="Mark selected dues as settled (paid outside the gateway)")
    def mark_settled_offline(self, request, queryset):
        run_action(self, request, queryset, "settle_due_offline", _mark_settled_offline, "Settled {count} due(s).")

    @admin.action(description="Waive selected dues")
    def waive_dues(self, request, queryset):
        run_action(self, request, queryset, "waive_due", _waive, "Waived {count} due(s).")
