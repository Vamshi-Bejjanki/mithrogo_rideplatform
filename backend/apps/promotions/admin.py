from django.contrib import admin
from django.db.models import Count, Q

from core.admin import AuditedModelAdmin, csv_export_action
from apps.promotions.models import PromoCode, PromoRedemption, RedemptionStatus


class PersonalFilter(admin.SimpleListFilter):
    title = "kind"
    parameter_name = "kind"

    def lookups(self, request, model_admin):
        return [("public", "Public codes"), ("personal", "Personal (referral rewards)")]

    def queryset(self, request, queryset):
        if self.value() == "public":
            return queryset.filter(assigned_user__isnull=True)
        if self.value() == "personal":
            return queryset.filter(assigned_user__isnull=False)
        return queryset


@admin.register(PromoCode)
class PromoCodeAdmin(AuditedModelAdmin):
    list_display = ("code", "discount_type", "value", "max_discount", "valid_until", "uses", "max_uses_total",
                    "assigned_user", "is_active")
    list_filter = ("is_active", "discount_type", PersonalFilter, "first_ride_only")
    search_fields = ("code", "description", "assigned_user__phone")
    raw_id_fields = ("assigned_user",)
    actions = ["export_csv"]
    export_csv = csv_export_action(
        [("code", "code"), ("type", "discount_type"), ("value", "value"), ("max_discount", "max_discount"),
         ("valid_until", "valid_until"), ("active", "is_active")],
        "promo-codes",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _uses=Count("redemptions", filter=Q(redemptions__status=RedemptionStatus.APPLIED))
        )

    @admin.display(description="Used", ordering="_uses")
    def uses(self, promo):
        return promo._uses


@admin.register(PromoRedemption)
class PromoRedemptionAdmin(admin.ModelAdmin):
    list_display = ("promo", "user", "ride", "discount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("promo__code", "user__phone")
    readonly_fields = [f.name for f in PromoRedemption._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
