import uuid

from django.conf import settings
from django.db import models


class PaymentType(models.TextChoices):
    RIDE_PAYMENT = "RIDE_PAYMENT", "Ride payment"
    CAPTAIN_SUBSCRIPTION = "CAPTAIN_SUBSCRIPTION", "Captain subscription"
    DUES_SETTLEMENT = "DUES_SETTLEMENT", "Platform dues settlement"
    WALLET_TOP_UP = "WALLET_TOP_UP", "Captain wallet top-up"
    CANCELLATION_FEE = "CANCELLATION_FEE", "Rider cancellation or no-show fee"


class PaymentStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    payment_type = models.CharField(max_length=30, choices=PaymentType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    provider = models.CharField(max_length=20)
    provider_order_id = models.CharField(max_length=64, unique=True)
    provider_payment_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.CREATED, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_payment_type_display()} ₹{self.amount} ({self.status})"
