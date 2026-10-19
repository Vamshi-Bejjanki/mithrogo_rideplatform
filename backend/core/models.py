from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PlatformConfig(TimeStampedModel):
    """Single row of operational settings. Edit in admin; never hard-code these values."""

    search_radius_km = models.DecimalField("search radius (km)", max_digits=5, decimal_places=2, default=3)
    offer_timeout_seconds = models.PositiveIntegerField("offer timeout (seconds)", default=15)
    max_offer_attempts = models.PositiveIntegerField("max captains offered per ride", default=5)
    location_freshness_seconds = models.PositiveIntegerField(
        "captain location freshness (seconds)",
        default=30,
        help_text="A captain whose last location is older than this is not matched.",
    )
    road_distance_factor = models.DecimalField(
        "road distance factor",
        max_digits=4,
        decimal_places=2,
        default="1.30",
        help_text="Straight-line distance is multiplied by this to estimate road distance.",
    )
    average_speed_kmph = models.DecimalField("average speed (km/h)", max_digits=5, decimal_places=2, default=20)
    min_trip_km = models.DecimalField("minimum trip distance (km)", max_digits=5, decimal_places=2, default="0.50")
    unpaid_dues_limit = models.DecimalField(
        "unpaid dues limit (₹)",
        max_digits=10,
        decimal_places=2,
        default=500,
        help_text="Captains whose pending platform dues exceed this cannot go online.",
    )
    service_timezone = models.CharField(
        "service timezone",
        max_length=64,
        default=settings.TIME_ZONE,
        help_text="Defines the business day for ride-share counting.",
    )

    # Ride safety
    require_start_pin = models.BooleanField(
        "require ride start PIN",
        default=True,
        help_text="The captain must enter the rider's 4-digit PIN to start the ride.",
    )
    start_pin_max_attempts = models.PositiveSmallIntegerField("wrong PIN attempts allowed", default=5)

    # Cancellations
    customer_cancel_fee = models.DecimalField(
        "customer cancellation fee (₹)",
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Charged when the rider cancels after the free window. 0 turns the fee off.",
    )
    cancel_free_window_seconds = models.PositiveIntegerField(
        "free cancellation window (seconds)",
        default=120,
        help_text="Time after a captain accepts during which the rider can cancel for free.",
    )
    customer_no_show_fee = models.DecimalField(
        "rider no-show fee (₹)",
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Charged when the captain cancels because the rider never came. 0 turns the fee off.",
    )
    no_show_wait_minutes = models.PositiveIntegerField(
        "no-show wait (minutes)",
        default=5,
        help_text="How long a captain must wait at pickup before cancelling for a no-show.",
    )
    block_booking_on_unpaid_fees = models.BooleanField(
        "block booking while fees are unpaid",
        default=True,
        help_text="Riders must pay outstanding cancellation fees before booking again.",
    )

    # Referrals
    referral_referee_reward = models.DecimalField(
        "referral reward for the new rider (₹)",
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Flat discount given to a rider who applies a referral code. 0 turns referrals off.",
    )
    referral_referrer_reward = models.DecimalField(
        "referral reward for the referrer (₹)",
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Flat discount given to the referrer after the new rider completes a first ride.",
    )
    referral_reward_valid_days = models.PositiveIntegerField("referral reward validity (days)", default=30)

    # Notifications and sharing
    plan_expiry_reminder_minutes = models.PositiveIntegerField(
        "plan expiry reminder (minutes before)",
        default=60,
        help_text="Captains are reminded this long before a daily plan runs out.",
    )
    share_link_grace_minutes = models.PositiveIntegerField(
        "trip share link grace (minutes)",
        default=30,
        help_text="A shared trip link keeps working this long after the ride ends.",
    )

    class Meta:
        verbose_name = "platform configuration"
        verbose_name_plural = "platform configuration"

    def __str__(self):
        return "Platform configuration"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # the singleton cannot be deleted

    @classmethod
    def load(cls):
        """The live configuration row. Re-read so values are database types, not Python defaults."""
        cls.objects.get_or_create(pk=1)
        return cls.objects.get(pk=1)


class AuditLog(models.Model):
    """Who changed what in the admin, and when. Written by core.audit.record."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=80)
    model = models.CharField(max_length=80)
    object_id = models.CharField(max_length=64)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.model}#{self.object_id}"
