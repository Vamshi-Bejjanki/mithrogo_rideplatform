from django.contrib import admin

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "payment_type", "amount", "status", "provider", "created_at")
    list_filter = ("payment_type", "status", "provider")
    search_fields = ("provider_order_id", "provider_payment_id", "user__phone")
    readonly_fields = [f.name for f in Payment._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
