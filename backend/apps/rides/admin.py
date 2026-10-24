import json

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.admin import AuditedModelAdmin, ReasonActionForm, action_reason, csv_export_action, run_action
from apps.rides.models import ACTIVE_STATUSES, CancelledBy, FareConfig, FeeStatus, Rating, Ride, RideEvent, RideOffer

RIDE_CSV = [
    ("id", "id"), ("status", "status"), ("vehicle_type", "vehicle_type"), ("customer", "customer__phone"),
    ("captain", "captain__user__phone"), ("pickup", "pickup_address"), ("drop", "drop_address"),
    ("distance_km", "estimated_distance_km"), ("fare", "final_fare"), ("discount", "discount_amount"),
    ("payable", "payable_fare"), ("payment_method", "payment_method"), ("payment_status", "payment_status"),
    ("cancelled_by", "cancelled_by"), ("cancellation_reason", "cancellation_reason"),
    ("cancellation_fee", "cancellation_fee"), ("requested_at", "requested_at"), ("completed_at", "completed_at"),
]


def _cancel_by_admin(request):
    from apps.rides import services
    from core.exceptions import DomainError

    reason = action_reason(request)

    def handler(ride, actor):
        if not reason:
            raise DomainError("Type a reason in the box next to the action.", code="reason_required")
        services.cancel_ride(ride, actor=actor, reason="CANCELLED_BY_ADMIN", cancelled_by=CancelledBy.ADMIN,
                             note=reason)

    return handler


def _waive(ride, actor):
    from apps.rides import services

    services.waive_fee(ride, actor)

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
    readonly_fields = ["route_map"] + [f.name for f in Ride._meta.fields if f.name != "start_pin"]
    exclude = ("start_pin",)  # staff never need the rider's PIN
    inlines = [RideEventInline, RideOfferInline]
    action_form = ReasonActionForm
    actions = ["cancel_rides", "waive_fees", "export_csv"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # rides change only through the state machine (and the actions below)

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Cancel selected rides (type the reason in the box)")
    def cancel_rides(self, request, queryset):
        run_action(self, request, queryset, "cancel_ride", _cancel_by_admin(request), "Cancelled {count} ride(s).")

    @admin.action(description="Waive cancellation fee")
    def waive_fees(self, request, queryset):
        run_action(self, request, queryset.filter(cancellation_fee_status=FeeStatus.UNPAID), "waive_fee", _waive,
                   "Waived {count} fee(s).")

    export_csv = csv_export_action(RIDE_CSV, "rides")

    @admin.display(description="Route")
    def route_map(self, ride):
        """Pickup, drop and the captain's recorded trail on a map."""
        trail = [[float(p.latitude), float(p.longitude)] for p in ride.locations.order_by("recorded_at")[:2000]]
        data = json.dumps({
            "pickup": [float(ride.pickup_latitude), float(ride.pickup_longitude)],
            "drop": [float(ride.drop_latitude), float(ride.drop_longitude)],
            "trail": trail,
        })
        return format_html(
            '''<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<div id="ride-map" style="height:320px;width:100%;max-width:720px;border-radius:8px"></div>
<p style="margin:4px 0 0;color:#666">{} location point(s) recorded.</p>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>(function(){{var d={};var m=L.map("ride-map");
L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",{{attribution:"&copy; OpenStreetMap"}}).addTo(m);
L.circleMarker(d.pickup,{{color:"#1565c0",radius:7}}).addTo(m).bindTooltip("Pickup");
L.circleMarker(d.drop,{{color:"#c62828",radius:7}}).addTo(m).bindTooltip("Drop");
if(d.trail.length){{L.polyline(d.trail,{{color:"#0b8f5a",weight:4}}).addTo(m);}}
m.fitBounds([d.pickup,d.drop].concat(d.trail),{{padding:[30,30]}});}})();</script>''',
            len(trail),
            mark_safe(data),
        )


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
