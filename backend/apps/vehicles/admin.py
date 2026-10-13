from django.contrib import admin

from core.admin import AuditedModelAdmin, run_action
from apps.vehicles.models import Vehicle
from apps.vehicles.services import unverify_vehicle, verify_vehicle


@admin.register(Vehicle)
class VehicleAdmin(AuditedModelAdmin):
    list_display = ("registration_number", "vehicle_type", "captain", "make", "model", "is_verified")
    list_filter = ("vehicle_type", "is_verified")
    search_fields = ("registration_number", "captain__user__phone")
    raw_id_fields = ("captain",)
    actions = ["verify_vehicles", "unverify_vehicles"]

    @admin.action(description="Verify selected vehicles")
    def verify_vehicles(self, request, queryset):
        run_action(self, request, queryset, "verify_vehicle", verify_vehicle, "Verified {count} vehicle(s).")

    @admin.action(description="Remove verification from selected vehicles")
    def unverify_vehicles(self, request, queryset):
        run_action(self, request, queryset, "unverify_vehicle", unverify_vehicle, "Unverified {count} vehicle(s).")
