from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class DiscountType(models.TextChoices):
    FLAT = "FLAT", "Flat amount (₹)"
    PERCENT = "PERCENT", "Percentage of fare"


class PromoCode(TimeStampedModel):
    """A discount riders enter at booking. Created in admin, or issued automatically as a referral reward."""

    code = models.CharField(max_length=24, unique=True, help_text="Stored in capitals. Riders type it in any case.")
    description = models.CharField(max_length=160, blank=True)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices)
    value = models.DecimalField(max_digits=8, decimal_places=2, help_text="Rupees for FLAT, percent for PERCENT.")
    max_discount = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, help_text="Cap for PERCENT codes."
    )
    min_fare = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    max_uses_total = models.PositiveIntegerField(null=True, blank=True, help_text="Empty means unlimited.")
    max_uses_per_user = models.PositiveIntegerField(default=1)
    first_ride_only = models.BooleanField(default=False)
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="personal_promos",
        help_text="Set for personal codes (referral rewards). Only this rider can use it.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class RedemptionStatus(models.TextChoices):
    RESERVED = "RESERVED", "Reserved (ride in progress)"
    APPLIED = "APPLIED", "Applied (ride completed)"
    RELEASED = "RELEASED", "Released (ride cancelled)"


class PromoRedemption(TimeStampedModel):
    promo = models.ForeignKey(PromoCode, on_delete=models.PROTECT, related_name="redemptions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="promo_redemptions")
    ride = models.OneToOneField("rides.Ride", on_delete=models.CASCADE, related_name="promo_redemption")
    discount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=RedemptionStatus.choices, default=RedemptionStatus.RESERVED, db_index=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["promo", "user", "status"])]

    def __str__(self):
        return f"{self.promo.code} on ride {str(self.ride_id)[:8]} ({self.status})"
