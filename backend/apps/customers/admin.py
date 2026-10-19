from django.contrib import admin

from core.admin import AuditedModelAdmin
from apps.customers.models import CustomerProfile, SavedPlace


@admin.register(CustomerProfile)
class CustomerProfileAdmin(AuditedModelAdmin):
    list_display = ("user", "emergency_contact_name", "emergency_contact_phone", "referral_code", "referred_by",
                    "updated_at")
    readonly_fields = ("referral_code", "referred_by", "referral_rewarded_at")
    search_fields = ("user__phone", "user__first_name", "user__last_name")
    raw_id_fields = ("user",)


@admin.register(SavedPlace)
class SavedPlaceAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "name", "address", "updated_at")
    list_filter = ("label",)
    search_fields = ("user__phone", "name", "address")
    raw_id_fields = ("user",)
