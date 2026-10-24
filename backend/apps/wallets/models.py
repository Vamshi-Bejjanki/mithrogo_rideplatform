from django.db import models

from core.models import TimeStampedModel


class CaptainWallet(TimeStampedModel):
    """Prepaid balance a captain uses to pay Mithrgo: plans and platform dues. Customers pay captains in cash."""

    captain = models.OneToOneField("captains.CaptainProfile", on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Wallet {self.captain} ₹{self.balance}"


class WalletTxnKind(models.TextChoices):
    TOP_UP = "TOP_UP", "Top-up"
    PLAN_PURCHASE = "PLAN_PURCHASE", "Plan purchase"
    DUES_SETTLEMENT = "DUES_SETTLEMENT", "Dues settlement"
    PROMO_CREDIT = "PROMO_CREDIT", "Promo discount credit (cash ride)"
    CANCELLATION_FEE = "CANCELLATION_FEE", "Rider cancellation fee credit"


class WalletTransaction(TimeStampedModel):
    """Append-only ledger. Positive amounts add money, negative amounts take it out."""

    wallet = models.ForeignKey(CaptainWallet, on_delete=models.PROTECT, related_name="transactions")
    kind = models.CharField(max_length=20, choices=WalletTxnKind.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=64)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["kind", "reference"], name="unique_wallet_txn_reference"),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} {self.amount} ({self.reference})"
