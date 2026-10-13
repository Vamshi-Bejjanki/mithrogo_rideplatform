from django.contrib import admin

from core.admin import AuditedModelAdmin
from apps.rides.models import ACTIVE_STATUSES, FareConfig, Rating, Ride, RideEvent, RideOffer


class LiveRideFilter(admin.SimpleListFilter):
    """Quick switch between rides in progress (the live view) and finished ones."""

    title = "live"
    parameter_name = "live"

    def lookups(self, request, model_admin):
        return [("active", "Live now"), ("finished", "Finished")]

    def queryset(self, request, queryset):
        if self.value() == "active":
            return queryset.filter(status__in=ACTIVE_STATUSES)
        if self.value() == "finished":
            return queryset.exclude(status__in=ACTIVE_STATUSES)
        return queryset


class RideEventInline(admin.TabularInline):
    """Timeline of every status change, read-only."""

    model = RideEvent
    extra = 0
    can_delete = False
    fields = ("created_at", "from_status", "to_status", "actor", "note")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class RideOfferInline(admin.TabularInline):
    model = RideOffer
    extra = 0
    can_delete = False
    fields = ("sequence", "captain", "distance_km", "status", "expires_at", "responded_at")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    """Live and historical rides. Rides are changed through the API state machine, never edited here."""

    list_display = (
        "id",
        "customer",
        "captain",
        "vehicle_type",
        "status",
        "estimated_fare",
        "final_fare",
        "payment_status",
        "is_platform_ride",
        "requested_at",
    )
    list_filter = (
        LiveRideFilter,
        "status",
        "vehicle_type",
        "payment_method",
        "payment_status",
        "is_platform_ride",
    )
    date_hierarchy = "requested_at"
    search_fields = ("id", "customer__phone", "captain__user__phone", "pickup_address", "drop_address")
    readonly_fields = [f.name for f in Ride._meta.fields]
    inlines = [RideEventInline, RideOfferInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FareConfig)
class FareConfigAdmin(AuditedModelAdmin):
    list_display = ("vehicle_type", "base_fare", "per_km", "minimum_fare", "platform_customer_fee", "is_active")
    list_filter = ("is_active",)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("ride", "customer", "captain", "rating", "created_at")
    list_filter = ("rating",)
    readonly_fields = [f.name for f in Rating._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
