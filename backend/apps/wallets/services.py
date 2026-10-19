from decimal import Decimal

from django.db import transaction

from core.exceptions import DomainError
from apps.wallets.models import CaptainWallet, WalletTransaction, WalletTxnKind


def get_wallet(captain):
    wallet, _ = CaptainWallet.objects.get_or_create(captain=captain)
    return wallet


def _locked_wallet(captain):
    wallet = get_wallet(captain)
    return CaptainWallet.objects.select_for_update().get(pk=wallet.pk)


def _post(wallet, amount, kind, reference):
    wallet.balance += amount
    wallet.save(update_fields=["balance", "updated_at"])
    WalletTransaction.objects.create(
        wallet=wallet, kind=kind, amount=amount, balance_after=wallet.balance, reference=reference
    )


@transaction.atomic
def debit(captain, amount, kind, reference):
    """Take money out of the wallet. Fails rather than going negative."""
    amount = Decimal(amount)
    wallet = _locked_wallet(captain)
    if wallet.balance < amount:
        raise DomainError("Not enough wallet balance. Top up to continue.", code="insufficient_balance")
    _post(wallet, -amount, kind, reference)
    return wallet


@transaction.atomic
def credit(captain, amount, kind, reference):
    wallet = _locked_wallet(captain)
    _post(wallet, Decimal(amount), kind, reference)
    return wallet


def start_top_up(captain, amount):
    """Create a gateway payment that adds to the wallet once the webhook confirms it."""
    from apps.payments.models import PaymentType
    from apps.payments.services import create_payment

    amount = Decimal(amount)
    if amount < Decimal("1"):
        raise DomainError("Top-up must be at least ₹1.", code="invalid_amount")
    return create_payment(captain.user, PaymentType.WALLET_TOP_UP, amount, {"captain_id": captain.pk})


def on_top_up_paid(payment):
    from apps.captains.models import CaptainProfile

    captain = CaptainProfile.objects.get(pk=payment.metadata["captain_id"])
    credit(captain, payment.amount, WalletTxnKind.TOP_UP, reference=str(payment.id))
