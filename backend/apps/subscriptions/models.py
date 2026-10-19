from django.core.exceptions import ValidationError
from django.db import models

from apps.vehicles.models import VehicleType
from core.models import TimeStampedModel


class PlanType(models.TextChoices):
    DAILY_FLAT = "DAILY_FLAT", "Daily flat fee"
    RIDE_SHARE = "RIDE_SHARE", "Ride share (1 ride a day)"


class SubscriptionPlan(TimeStampedModel):
    """Captain plans. Amounts and counts live here so they can be changed without a deploy."""

    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration_hours = models.PositiveIntegerField(
        null=True, blank=True, help_text="Daily plans only: how long one purchase lasts."
    )
    vehicle_type = models.CharField(
        max_length=10,
        choices=VehicleType.choices,
        null=True,
        blank=True,
        help_text="The vehicle type this plan is for.",
    )
    qualifying_rides = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Ride-share only: the platform ride is one of the first N completed rides."
    )
    shortfall_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="Ride-share only: owed after a shortfall day."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.plan_type == PlanType.DAILY_FLAT:
            if not self.duration_hours:
                raise ValidationError({"duration_hours": "Daily plans need a duration in hours."})
            if not self.vehicle_type:
                raise ValidationError({"vehicle_type": "Daily plans need a vehicle type."})
        if self.plan_type == PlanType.RIDE_SHARE:
            if not self.vehicle_type:
                raise ValidationError({"vehicle_type": "Ride-share plans need a vehicle type."})
            if not self.qualifying_rides or self.qualifying_rides < 2:
                raise ValidationError({"qualifying_rides": "Ride-share plans need at least 2 qualifying rides."})
            if self.shortfall_fee is None:
                raise ValidationError({"shortfall_fee": "Ride-share plans need a shortfall fee."})


class SubStatus(models.TextChoices):
    PENDING = "PENDING", "Pending payment"
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"
    FAILED = "FAILED", "Failed"


class CaptainSubscription(TimeStampedModel):
    captain = models.ForeignKey("captains.CaptainProfile", on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    start_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Empty for ride-share (open-ended).")
    status = models.CharField(max_length=12, choices=SubStatus.choices, default=SubStatus.PENDING, db_index=True)
    payment = models.ForeignKey(
        "payments.Payment", null=True, blank=True, on_delete=models.SET_NULL, related_name="subscriptions"
    )
    penalty_pending = models.BooleanField(
        default=False, help_text="Set after a shortfall day; cleared when the next day's first ride is taken."
    )
    expiry_reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["captain", "status"])]

    def __str__(self):
        return f"{self.captain} – {self.plan.code} ({self.status})"


class DayStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class RideShareDay(TimeStampedModel):
    captain = models.ForeignKey("captains.CaptainProfile", on_delete=models.CASCADE, related_name="ride_share_days")
    subscription = models.ForeignKey(CaptainSubscription, on_delete=models.PROTECT, related_name="ride_share_days")
    service_date = models.DateField()
    qualifying_rides = models.PositiveSmallIntegerField()
    completed_rides = models.PositiveIntegerField(default=0)
    platform_ride = models.ForeignKey(
        "rides.Ride", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    surrendered_ride = models.ForeignKey(
        "rides.Ride", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    status = models.CharField(max_length=8, choices=DayStatus.choices, default=DayStatus.OPEN, db_index=True)
    shortfall = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["captain", "service_date"], name="one_ride_share_day_per_captain"),
        ]

    def __str__(self):
        return f"{self.captain} {self.service_date}"


class DueType(models.TextChoices):
    RIDE_SHARE = "RIDE_SHARE", "Platform ride share"
    SHORTFALL_FEE = "SHORTFALL_FEE", "Shortfall fee"


class DueStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SETTLED = "SETTLED", "Settled"
    WAIVED = "WAIVED", "Waived"


class PlatformDue(TimeStampedModel):
    """Ledger of money a captain owes the platform."""

    captain = models.ForeignKey("captains.CaptainProfile", on_delete=models.CASCADE, related_name="platform_dues")
    ride = models.ForeignKey(
        "rides.Ride", null=True, blank=True, on_delete=models.SET_NULL, related_name="platform_dues"
    )
    due_type = models.CharField(max_length=20, choices=DueType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=DueStatus.choices, default=DueStatus.PENDING, db_index=True)
    payment = models.ForeignKey(
        "payments.Payment", null=True, blank=True, on_delete=models.SET_NULL, related_name="platform_dues"
    )
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["captain", "status"])]

    def __str__(self):
        return f"{self.get_due_type_display()} ₹{self.amount} ({self.status})"
