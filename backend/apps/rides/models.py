import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from core.models import TimeStampedModel
from apps.vehicles.models import VehicleType


class RideStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    SEARCHING = "SEARCHING", "Searching"
    ACCEPTED = "ACCEPTED", "Accepted"
    CAPTAIN_ARRIVED = "CAPTAIN_ARRIVED", "Captain arrived"
    STARTED = "STARTED", "Started"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


ACTIVE_STATUSES = [
    RideStatus.REQUESTED,
    RideStatus.SEARCHING,
    RideStatus.ACCEPTED,
    RideStatus.CAPTAIN_ARRIVED,
    RideStatus.STARTED,
]
# Statuses in which a captain is engaged on a ride (BUSY).
IN_PROGRESS_STATUSES = [RideStatus.ACCEPTED, RideStatus.CAPTAIN_ARRIVED, RideStatus.STARTED]


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Cash"
    ONLINE = "ONLINE", "Online"


class RidePaymentStatus(models.TextChoices):
    UNPAID = "UNPAID", "Unpaid"
    PAID = "PAID", "Paid"


class ShareReason(models.TextChoices):
    SURRENDERED = "SURRENDERED", "Captain surrendered"
    AUTO_5TH = "AUTO_5TH", "Automatic (qualifying ride)"
    PENALTY_FIRST_RIDE = "PENALTY_FIRST_RIDE", "Penalty (after shortfall day)"


class OfferStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"


class FareConfig(TimeStampedModel):
    """Fare rules per vehicle type. Editable in admin. Fares are never taken from the client."""

    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices, unique=True)
    base_fare = models.DecimalField(max_digits=8, decimal_places=2)
    per_km = models.DecimalField(max_digits=8, decimal_places=2)
    minimum_fare = models.DecimalField(max_digits=8, decimal_places=2)
    platform_customer_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, help_text="Added to every customer fare."
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Fare {self.get_vehicle_type_display()}"


class Ride(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="rides")
    captain = models.ForeignKey(
        "captains.CaptainProfile", null=True, blank=True, on_delete=models.PROTECT, related_name="rides"
    )
    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices)

    pickup_address = models.CharField(max_length=255)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    drop_address = models.CharField(max_length=255)
    drop_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    drop_longitude = models.DecimalField(max_digits=9, decimal_places=6)

    estimated_distance_km = models.DecimalField(max_digits=8, decimal_places=2)
    estimated_duration_minutes = models.PositiveIntegerField()
    estimated_fare = models.DecimalField(max_digits=10, decimal_places=2)
    final_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.ONLINE)
    payment_status = models.CharField(
        max_length=10, choices=RidePaymentStatus.choices, default=RidePaymentStatus.UNPAID
    )

    status = models.CharField(max_length=20, choices=RideStatus.choices, default=RideStatus.REQUESTED, db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=60, blank=True)

    is_platform_ride = models.BooleanField(default=False)
    platform_share_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    share_reason = models.CharField(max_length=20, choices=ShareReason.choices, null=True, blank=True)

    idempotency_key = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["captain", "created_at"]),
        ]
        constraints = [
            # DB backstop: one non-terminal ride per customer, one in-progress ride per captain.
            models.UniqueConstraint(
                fields=["customer"],
                condition=Q(status__in=ACTIVE_STATUSES),
                name="one_active_ride_per_customer",
            ),
            models.UniqueConstraint(
                fields=["captain"],
                condition=Q(status__in=IN_PROGRESS_STATUSES),
                name="one_active_ride_per_captain",
            ),
            models.UniqueConstraint(
                fields=["customer", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="unique_ride_idempotency_key",
            ),
        ]

    def __str__(self):
        return f"Ride {str(self.id)[:8]} ({self.status})"


class RideEvent(models.Model):
    """Append-only status history for support and disputes."""

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class RideOffer(TimeStampedModel):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name="offers")
    captain = models.ForeignKey("captains.CaptainProfile", on_delete=models.CASCADE, related_name="ride_offers")
    sequence = models.PositiveSmallIntegerField()
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(max_length=10, choices=OfferStatus.choices, default=OfferStatus.PENDING)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["ride", "captain"], name="one_offer_per_captain_per_ride")]
        indexes = [models.Index(fields=["captain", "status"])]


class RideLocation(models.Model):
    """Location samples taken while a captain is on a ride. Live position lives on CaptainProfile."""

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name="locations")
    captain = models.ForeignKey("captains.CaptainProfile", on_delete=models.CASCADE, related_name="+")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    heading = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    speed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["ride", "recorded_at"])]


class Rating(models.Model):
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE, related_name="rating")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    captain = models.ForeignKey("captains.CaptainProfile", on_delete=models.CASCADE, related_name="ratings")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
