from decimal import Decimal

import pytest

from apps.payments import services as payment_services
from apps.subscriptions import services as subscription_services
from apps.subscriptions.models import CaptainSubscription, DueStatus, DueType, PlatformDue, SubStatus
from apps.wallets import services as wallet_services
from apps.wallets.models import WalletTransaction, WalletTxnKind
from core.exceptions import DomainError
from tests.helpers import make_captain


def top_up(captain, amount):
    """Add money the way production does: a gateway payment confirmed by the webhook."""
    payment = wallet_services.start_top_up(captain, amount)
    payment_services.mark_success(payment.provider_order_id, f"pay_{payment.id.hex[:12]}", payment.amount)
    return payment


@pytest.mark.django_db
def test_confirmed_top_up_credits_the_wallet_once():
    captain = make_captain(plan=None, location=None, online=False)

    payment = top_up(captain, "100")
    payment_services.mark_success(payment.provider_order_id, "pay_repeat", payment.amount)

    wallet = wallet_services.get_wallet(captain)
    assert wallet.balance == Decimal("100.00")
    assert WalletTransaction.objects.filter(wallet=wallet, kind=WalletTxnKind.TOP_UP).count() == 1


@pytest.mark.django_db
def test_top_up_below_one_rupee_is_refused():
    captain = make_captain(plan=None, location=None, online=False)

    with pytest.raises(DomainError) as info:
        wallet_services.start_top_up(captain, "0")
    assert info.value.code == "invalid_amount"


@pytest.mark.django_db
def test_daily_plan_is_paid_from_the_wallet_and_activates():
    captain = make_captain(plan=None, location=None, online=False)
    top_up(captain, "50")

    sub = subscription_services.pay_daily_plan_from_wallet(captain, "DAILY_BIKE")

    sub.refresh_from_db()
    assert sub.status == SubStatus.ACTIVE
    assert wallet_services.get_wallet(captain).balance == Decimal("20.00")


@pytest.mark.django_db
def test_plan_purchase_without_enough_balance_creates_nothing():
    captain = make_captain(plan=None, location=None, online=False)
    top_up(captain, "10")

    with pytest.raises(DomainError) as info:
        subscription_services.pay_daily_plan_from_wallet(captain, "DAILY_BIKE")

    assert info.value.code == "insufficient_balance"
    assert not CaptainSubscription.objects.filter(captain=captain).exists()
    assert wallet_services.get_wallet(captain).balance == Decimal("10.00")


@pytest.mark.django_db
def test_pending_dues_are_settled_from_the_wallet():
    captain = make_captain(plan=None, location=None, online=False)
    top_up(captain, "100")
    PlatformDue.objects.create(captain=captain, due_type=DueType.SHORTFALL_FEE, amount=Decimal("30.00"))

    paid = subscription_services.pay_dues_from_wallet(captain)

    assert paid == Decimal("30.00")
    assert PlatformDue.objects.get(captain=captain).status == DueStatus.SETTLED
    assert wallet_services.get_wallet(captain).balance == Decimal("70.00")


@pytest.mark.django_db
def test_paying_dues_with_nothing_owed_is_refused():
    captain = make_captain(plan=None, location=None, online=False)

    with pytest.raises(DomainError) as info:
        subscription_services.pay_dues_from_wallet(captain)
    assert info.value.code == "no_dues"


@pytest.mark.django_db
def test_wallet_endpoint_shows_balance_and_history(as_user):
    captain = make_captain(plan=None, location=None, online=False)
    top_up(captain, "75")

    body = as_user(captain.user).get("/api/v1/captains/wallet/").json()

    assert Decimal(body["balance"]) == Decimal("75.00")
    assert body["transactions"][0]["kind"] == WalletTxnKind.TOP_UP
