from django.contrib import admin
from django.utils.html import format_html, format_html_join

from core.admin import AuditedModelAdmin, ReasonActionForm, action_reason, csv_export_action, run_action
from core.exceptions import DomainError
from apps.captains import services
from apps.captains.models import CaptainProfile, KycDocument
from apps.vehicles.models import Vehicle


IMAGE_TYPES = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def _preview(doc):
    if not doc.file:
        return "-"
    url = doc.file.url
    if url.lower().endswith(IMAGE_TYPES):
        return format_html('<a href="{}" target="_blank"><img src="{}" style="max-height:120px;max-width:200px;'
                           'border-radius:4px;border:1px solid #ddd"></a>', url, url)
    return format_html('<a href="{}" target="_blank">Open file</a>', url)


class KycDocumentInline(admin.TabularInline):
    model = KycDocument
    extra = 0
    fields = ("doc_type", "preview", "file", "created_at")
    readonly_fields = ("preview", "created_at")

    @admin.display(description="Preview")
    def preview(self, doc):
        return _preview(doc)


class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 0
    fields = ("vehicle_type", "registration_number", "make", "model", "color", "is_verified")


@admin.register(CaptainProfile)
class CaptainProfileAdmin(AuditedModelAdmin):
    list_display = ("user", "kyc_status", "online_status", "rating", "total_rides", "cancelled_rides",
                    "last_location_at")
    list_filter = ("kyc_status", "online_status")
    search_fields = ("user__phone", "user__first_name", "user__last_name", "license_number")
    raw_id_fields = ("user",)
    readonly_fields = ("documents_preview", "online_status", "rating", "total_rides", "cancelled_rides",
                       "kyc_rejection_reason", "last_location_at", "created_at", "updated_at")
    inlines = [KycDocumentInline, VehicleInline]
    action_form = ReasonActionForm
    actions = ["approve_kyc", "reject_kyc", "suspend_captains", "reactivate_captains", "export_csv"]
    export_csv = csv_export_action(
        [("phone", "user__phone"), ("name", "user__full_name"), ("kyc_status", "kyc_status"),
         ("online_status", "online_status"), ("rating", "rating"), ("total_rides", "total_rides"),
         ("cancelled_rides", "cancelled_rides"), ("joined", "created_at")],
        "captains",
    )

    @admin.display(description="Documents")
    def documents_preview(self, captain):
        docs = captain.kyc_documents.all()
        if not docs:
            return "No documents uploaded yet."
        return format_html_join(
            "", '<div style="display:inline-block;margin:0 12px 12px 0;text-align:center">{}<br><small>{}</small></div>',
            ((_preview(doc), doc.get_doc_type_display()) for doc in docs),
        )

    @admin.action(description="Approve KYC")
    def approve_kyc(self, request, queryset):
        run_action(self, request, queryset, "approve_kyc", services.approve_kyc, "Approved {count} captain(s).")

    @admin.action(description="Reject KYC (type the reason in the box)")
    def reject_kyc(self, request, queryset):
        reason = action_reason(request)

        def handler(captain, actor):
            if not reason:
                raise DomainError("Type the reason in the box next to the action. The captain sees it.",
                                  code="reason_required")
            services.reject_kyc(captain, actor, reason)

        run_action(self, request, queryset, "reject_kyc", handler, "Rejected {count} captain(s).")

    @admin.action(description="Suspend selected captains")
    def suspend_captains(self, request, queryset):
        run_action(self, request, queryset, "suspend_captain", services.suspend_captain, "Suspended {count} captain(s).")

    @admin.action(description="Reactivate selected captains")
    def reactivate_captains(self, request, queryset):
        run_action(
            self, request, queryset, "reactivate_captain", services.reactivate_captain, "Reactivated {count} captain(s)."
        )
