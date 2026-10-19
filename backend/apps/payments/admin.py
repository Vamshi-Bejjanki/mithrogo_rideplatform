from django.contrib import admin

from core.admin import csv_export_action
from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "payment_type", "amount", "status", "provider", "created_at")
    list_filter = ("payment_type", "status", "provider")
    search_fields = ("provider_order_id", "provider_payment_id", "user__phone")
    readonly_fields = [f.name for f in Payment._meta.fields]
    date_hierarchy = "created_at"
    actions = ["export_csv"]
    export_csv = csv_export_action(
        [("id", "id"), ("user", "user__phone"), ("type", "payment_type"), ("amount", "amount"), ("status", "status"),
         ("provider", "provider"), ("order_id", "provider_order_id"), ("payment_id", "provider_payment_id"),
         ("created_at", "created_at"), ("updated_at", "updated_at")],
        "payments",
    )

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False
