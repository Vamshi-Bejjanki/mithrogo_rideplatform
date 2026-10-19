import json
from decimal import Decimal

import pytest

from apps.payments import services as payment_services
from apps.payments.models import Payment, PaymentStatus, PaymentType
from apps.subscriptions import services as subscription_services
from apps.subscriptions.models import CaptainSubscription, DueStatus, PlatformDue, SubStatus
from apps.users.models import Role
from tests.helpers import captured_event, make_captain, make_user, send_webhook


@pytest.fixture
def rider(db):
    return make_user(Role.CUSTOMER)


@pytest.mark.django_db
def test_webhook_with_a_bad_signature_is_refused(api, rider):
    payment = payment_services.create_payment(rider, PaymentType.RIDE_PAYMENT, Decimal("50"), {"ride_id": "x"})
    body = json.dumps(captured_event(payment)).encode()

    response = api.post(
        "/api/v1/payments/webhook/",
        data=body,
        content_type="application/json",
        HTTP_X_PAYMENT_SIGNATURE="not-the-right-signature",
    )

    assert response.status_code == 401
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING


@pytest.mark.django_db
def test_webhook_for_an_unknown_order_is_rejected(api):
    event = {
        "event": "payment.captured",
        "provider_order_id": "does-not-exist",
        "provider_payment_id": "pay_1",
        "amount": "30.00",
    }

    response = send_webhook(api, event)

    assert response.status_code == 400
    assert response.json()["code"] == "unknown_order"


@pytest.mark.django_db
def test_amount_must_match_the_order(api, rider):
    payment = payment_services.create_payment(rider, PaymentType.RIDE_PAYMENT, Decimal("50"), {"ride_id": "x"})
    event = {**captured_event(payment), "amount": "1.00"}

    response = send_webhook(api, event)

    assert response.status_code == 400
    assert response.json()["code"] == "amount_mismatch"
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING


@pytest.mark.django_db
def test_duplicate_webhook_does_not_activate_twice(api):
    captain = make_captain(plan=None, location=None, online=False)
    sub, payment = subscription_services.create_daily_subscription_payment(captain, "DAILY_BIKE")
    event = captured_event(payment)

    first = send_webhook(api, event)
    second = send_webhook(api, event)

    assert first.status_code == 200 and second.status_code == 200
    sub.refresh_from_db()
    assert sub.status == SubStatus.ACTIVE
    assert CaptainSubscription.objects.filter(captain=captain, status=SubStatus.ACTIVE).count() == 1
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.SUCCESS


@pytest.mark.django_db
def test_captain_can_buy_daily_plan_and_verify_status_before_and_after_payment(api, as_user):
    captain = make_captain(plan=None, location=None, online=False)
    captain_api = as_user(captain.user)

    created = captain_api.post("/api/v1/captains/subscription/create-payment/", {"plan_code": "DAILY_BIKE"}, format="json")
    assert created.status_code == 201
    payment_id = created.json()["payment"]["id"]
    before = captain_api.post("/api/v1/captains/subscription/verify-payment/", {"payment_id": payment_id}, format="json")

    payment = Payment.objects.get(pk=payment_id)
    send_webhook(api, captured_event(payment))
    after = captain_api.post("/api/v1/captains/subscription/verify-payment/", {"payment_id": payment_id}, format="json")

    assert before.json()["activated"] is False
    assert after.json()["activated"] is True
    assert after.json()["payment"]["status"] == "SUCCESS"


@pytest.mark.django_db
def test_mobile_success_alone_never_activates_a_subscription(as_user):
    captain = make_captain(plan=None, location=None, online=False)
    from apps.subscriptions import services as subscription_services

    sub, payment = subscription_services.create_daily_subscription_payment(captain, "DAILY_BIKE")
    response = as_user(captain.user).post(
        "/api/v1/captains/subscription/verify-payment/", {"payment_id": str(payment.id)}, format="json"
    )

    sub.refresh_from_db()
    assert response.json()["activated"] is False
    assert sub.status == SubStatus.PENDING


@pytest.mark.django_db
def test_payment_details_are_visible_only_to_their_owner(api, rider, as_user):
    payment = payment_services.create_payment(rider, PaymentType.RIDE_PAYMENT, Decimal("50"), {"ride_id": "x"})
    stranger = make_user(Role.CUSTOMER)

    own = as_user(rider).get(f"/api/v1/payments/{payment.id}/")
    other = as_user(stranger).get(f"/api/v1/payments/{payment.id}/")

    assert own.status_code == 200
    assert other.status_code == 404


@pytest.mark.django_db
def test_paying_dues_settles_exactly_the_pending_dues(api):
    captain = make_captain(plan="daily", location=None, online=False)
    PlatformDue.objects.create(captain=captain, due_type="RIDE_SHARE", amount=Decimal("40.00"))
    PlatformDue.objects.create(captain=captain, due_type="RIDE_SHARE", amount=Decimal("35.00"))
    from apps.subscriptions import services as subscription_services

    payment = subscription_services.create_dues_payment(captain)
    assert payment.amount == Decimal("75.00")
    send_webhook(api, captured_event(payment))

    assert PlatformDue.objects.filter(captain=captain, status=DueStatus.SETTLED).count() == 2
    assert PlatformDue.objects.filter(captain=captain, status=DueStatus.PENDING).count() == 0
