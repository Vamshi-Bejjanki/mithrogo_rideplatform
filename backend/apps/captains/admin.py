from django.contrib import admin

from core.admin import AuditedModelAdmin, run_action
from apps.captains import services
from apps.captains.models import CaptainProfile, KycDocument
from apps.vehicles.models import Vehicle


class KycDocumentInline(admin.TabularInline):
    model = KycDocument
    extra = 0
    fields = ("doc_type", "file", "created_at")
    readonly_fields = ("created_at",)


class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 0
    fields = ("vehicle_type", "registration_number", "make", "model", "color", "is_verified")


@admin.register(CaptainProfile)
class CaptainProfileAdmin(AuditedModelAdmin):
    list_display = ("user", "kyc_status", "online_status", "rating", "total_rides", "last_location_at")
    list_filter = ("kyc_status", "online_status")
    search_fields = ("user__phone", "user__first_name", "user__last_name", "license_number")
    raw_id_fields = ("user",)
    readonly_fields = ("online_status", "rating", "total_rides", "last_location_at", "created_at", "updated_at")
    inlines = [KycDocumentInline, VehicleInline]
    actions = ["approve_kyc", "reject_kyc", "suspend_captains", "reactivate_captains"]

    @admin.action(description="Approve KYC")
    def approve_kyc(self, request, queryset):
        run_action(self, request, queryset, "approve_kyc", services.approve_kyc, "Approved {count} captain(s).")

    @admin.action(description="Reject KYC")
    def reject_kyc(self, request, queryset):
        run_action(self, request, queryset, "reject_kyc", services.reject_kyc, "Rejected {count} captain(s).")

    @admin.action(description="Suspend selected captains")
    def suspend_captains(self, request, queryset):
        run_action(self, request, queryset, "suspend_captain", services.suspend_captain, "Suspended {count} captain(s).")

    @admin.action(description="Reactivate selected captains")
    def reactivate_captains(self, request, queryset):
        run_action(
            self, request, queryset, "reactivate_captain", services.reactivate_captain, "Reactivated {count} captain(s)."
        )
