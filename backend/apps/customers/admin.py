from django.contrib import admin

from core.admin import AuditedModelAdmin
from apps.customers.models import CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(AuditedModelAdmin):
    list_display = ("user", "emergency_contact_name", "emergency_contact_phone", "updated_at")
    search_fields = ("user__phone", "user__first_name", "user__last_name")
    raw_id_fields = ("user",)
