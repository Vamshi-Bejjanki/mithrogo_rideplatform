from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from core.models import PlatformConfig
from apps.captains.models import CaptainProfile, OnlineStatus
from apps.payments.models import Payment, PaymentType
from apps.rides import services
from apps.rides.models import FeeStatus, Ride, RideStatus
from apps.wallets.services import get_wallet
from tests.helpers import NEAR_PICKUP, captured_event, make_captain, ride_data, ride_payload, send_webhook

pytestmark = pytest.mark.django_db


def client_for(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def arrived_ride(customer, captain):
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    services.mark_arrived(captain, ride.id)
    return Ride.objects.get(pk=ride.id)


def set_config(**values):
    config = PlatformConfig.load()
    for key, value in values.items():
        setattr(config, key, value)
    config.save()


# ---------- start PIN ----------

def test_every_ride_gets_a_four_digit_pin_the_rider_can_see(customer, captain):
    ride = services.create_ride(customer, ride_data())
    assert len(ride.start_pin) == 4 and ride.start_pin.isdigit()

    body = client_for(customer).get(f"/api/v1/rides/{ride.id}/").json()
    assert body["start_pin"] == ride.start_pin
    assert client_for(customer).get(f"/api/v1/rides/{ride.id}/tracking/").json()["start_pin"] == ride.start_pin


def test_captain_never_sees_the_pin(customer, captain):
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    body = client_for(captain.user).get(f"/api/v1/captains/rides/{ride.id}/").json()
    assert "start_pin" not in body


def test_ride_cannot_start_without_the_right_pin(customer, captain):
    ride = arrived_ride(customer, captain)
    api = client_for(captain.user)

    missing = api.post(f"/api/v1/captains/rides/{ride.id}/start/", {}, format="json")
    assert missing.status_code == 400 and missing.json()["code"] == "pin_required"

    wrong = "0000" if ride.start_pin != "0000" else "1111"
    bad = api.post(f"/api/v1/captains/rides/{ride.id}/start/", {"pin": wrong}, format="json")
    assert bad.status_code == 400 and bad.json()["code"] == "wrong_pin"

    good = api.post(f"/api/v1/captains/rides/{ride.id}/start/", {"pin": ride.start_pin}, format="json")
    assert good.status_code == 200 and good.json()["status"] == "STARTED"
    # Once started, the PIN is no longer shown to the rider either.
    assert client_for(customer).get(f"/api/v1/rides/{ride.id}/").json()["start_pin"] is None


def test_pin_locks_after_too_many_wrong_attempts(customer, captain):
    set_config(start_pin_max_attempts=2)
    ride = arrived_ride(customer, captain)
    wrong = "0000" if ride.start_pin != "0000" else "1111"
    for _ in range(2):
        with pytest.raises(Exception):
            services.start_ride(captain, ride.id, pin=wrong)
    locked = client_for(captain.user).post(
        f"/api/v1/captains/rides/{ride.id}/start/", {"pin": ride.start_pin}, format="json"
    )
    assert locked.status_code == 429 and locked.json()["code"] == "pin_locked"


def test_pin_can_be_turned_off(customer, captain):
    set_config(require_start_pin=False)
    ride = arrived_ride(customer, captain)
    assert services.start_ride(captain, ride.id).status == RideStatus.STARTED


# ---------- rider cancellation ----------

def test_rider_cancels_with_a_reason_and_note(customer, captain):
    ride = services.create_ride(customer, ride_data())
    response = client_for(customer).post(
        f"/api/v1/rides/{ride.id}/cancel/", {"reason": "WRONG_PICKUP", "note": "Typed the wrong gate"}, format="json"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CANCELLED"
    assert body["cancellation_reason"] == "WRONG_PICKUP"
    assert body["cancelled_by"] == "CUSTOMER"
    assert body["cancellation_note"] == "Typed the wrong gate"
    assert body["cancellation_fee_status"] == "NONE"


def test_cancel_preview_lists_reasons_and_the_fee(customer, captain):
    ride = services.create_ride(customer, ride_data())
    preview = client_for(customer).get(f"/api/v1/rides/{ride.id}/cancel/").json()
    assert preview["can_cancel"] is True and preview["fee"] == "0"
    assert {"code": "CHANGED_MIND", "label": "Changed my mind"} in preview["reasons"]


def test_fee_only_after_the_free_window(customer, captain, clock):
    set_config(customer_cancel_fee=Decimal("25.00"), cancel_free_window_seconds=120)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)

    clock.advance(seconds=60)
    assert services.customer_cancel_fee(Ride.objects.get(pk=ride.id), "CHANGED_MIND") == 0
    clock.advance(seconds=120)
    ride = services.customer_cancel(customer, ride.id, "CHANGED_MIND")
    assert ride.cancellation_fee == Decimal("25.00")
    assert ride.cancellation_fee_status == FeeStatus.UNPAID
    captain.refresh_from_db()
    assert captain.online_status == OnlineStatus.ONLINE  # freed for the next request


def test_no_fee_when_the_captain_asked_or_for_safety(customer, captain, clock):
    set_config(customer_cancel_fee=Decimal("25.00"), cancel_free_window_seconds=0)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    clock.advance(seconds=30)
    ride = services.customer_cancel(customer, ride.id, "CAPTAIN_ASKED")
    assert ride.cancellation_fee == 0 and ride.cancellation_fee_status == FeeStatus.NONE


def test_unpaid_fee_blocks_booking_until_paid_and_credits_the_captain(customer, captain, clock):
    set_config(customer_cancel_fee=Decimal("25.00"), cancel_free_window_seconds=0)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    clock.advance(seconds=5)
    services.customer_cancel(customer, ride.id, "CHANGED_MIND")

    api = client_for(customer)
    blocked = api.post("/api/v1/rides/", ride_payload(), format="json")
    assert blocked.status_code == 409 and blocked.json()["code"] == "unpaid_cancellation_fee"
    assert [r["id"] for r in api.get("/api/v1/rides/outstanding-fees/").json()] == [str(ride.id)]

    pay = api.post(f"/api/v1/rides/{ride.id}/fee-payment/")
    assert pay.status_code == 201 and pay.json()["amount"] == "25.00"
    payment = Payment.objects.get(pk=pay.json()["id"])
    assert payment.payment_type == PaymentType.CANCELLATION_FEE
    assert send_webhook(api, captured_event(payment)).status_code == 200

    assert Ride.objects.get(pk=ride.id).cancellation_fee_status == FeeStatus.PAID
    assert get_wallet(captain).balance == Decimal("25.00")
    assert api.post("/api/v1/rides/", ride_payload(), format="json").status_code == 201


def test_admin_can_waive_a_fee(customer, captain, clock):
    set_config(customer_cancel_fee=Decimal("25.00"), cancel_free_window_seconds=0)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    clock.advance(seconds=5)
    ride = services.customer_cancel(customer, ride.id, "CHANGED_MIND")
    services.waive_fee(ride)
    assert Ride.objects.get(pk=ride.id).cancellation_fee_status == FeeStatus.WAIVED
    assert not services.outstanding_fees(customer).exists()


# ---------- captain cancellation ----------

def test_captain_cancel_sends_the_ride_to_the_next_captain(customer, captain):
    second = make_captain(location=NEAR_PICKUP)
    ride = services.create_ride(customer, ride_data())
    first = Ride.objects.get(pk=ride.id).offers.get().captain
    other = second if first.pk == captain.pk else captain
    services.accept_offer(first, ride.id)

    response = client_for(first.user).post(
        f"/api/v1/captains/rides/{ride.id}/cancel/", {"reason": "VEHICLE_ISSUE"}, format="json"
    )
    assert response.status_code == 200

    ride = Ride.objects.get(pk=ride.id)
    assert ride.status == RideStatus.SEARCHING
    assert ride.captain_id is None
    assert ride.offers.filter(captain=other, status="PENDING").exists()
    first = CaptainProfile.objects.get(pk=first.pk)
    assert first.cancelled_rides == 1
    assert first.online_status == OnlineStatus.ONLINE
    assert customer.notifications.filter(type="CAPTAIN_CANCELLED").exists()


def test_no_show_needs_the_wait_then_charges_the_rider(customer, captain, clock):
    set_config(customer_no_show_fee=Decimal("20.00"), no_show_wait_minutes=5)
    ride = arrived_ride(customer, captain)
    api = client_for(captain.user)

    early = api.post(f"/api/v1/captains/rides/{ride.id}/cancel/", {"reason": "CUSTOMER_NOT_AT_PICKUP"}, format="json")
    assert early.status_code == 409 and early.json()["code"] == "no_show_wait"

    clock.advance(minutes=6)
    late = api.post(f"/api/v1/captains/rides/{ride.id}/cancel/", {"reason": "CUSTOMER_NOT_AT_PICKUP"}, format="json")
    assert late.status_code == 200
    ride = Ride.objects.get(pk=ride.id)
    assert ride.status == RideStatus.CANCELLED
    assert ride.cancelled_by == "CAPTAIN"
    assert ride.cancellation_fee == Decimal("20.00")
    captain.refresh_from_db()
    assert captain.cancelled_rides == 0  # a no-show is not the captain's fault


def test_captain_cannot_cancel_a_started_ride(customer, captain):
    ride = arrived_ride(customer, captain)
    services.start_ride(captain, ride.id, pin=ride.start_pin)
    response = client_for(captain.user).post(
        f"/api/v1/captains/rides/{ride.id}/cancel/", {"reason": "OTHER"}, format="json"
    )
    assert response.status_code == 409


# ---------- rated flag and sharing ----------

def test_ride_detail_says_whether_it_was_rated(customer, captain):
    ride = arrived_ride(customer, captain)
    services.start_ride(captain, ride.id, pin=ride.start_pin)
    services.complete_ride(captain, ride.id)
    api = client_for(customer)
    assert api.get(f"/api/v1/rides/{ride.id}/").json()["is_rated"] is False
    api.post(f"/api/v1/rides/{ride.id}/rating/", {"rating": 4, "comment": "Good"}, format="json")
    body = api.get(f"/api/v1/rides/{ride.id}/").json()
    assert body["is_rated"] is True and body["my_rating"] == {"rating": 4, "comment": "Good"}


def test_shared_trip_link_is_public_limited_and_revocable(customer, captain):
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    api = client_for(customer)
    share = api.post(f"/api/v1/rides/{ride.id}/share/")
    assert share.status_code == 201
    token = share.json()["token"]
    assert share.json()["url"].endswith(f"/api/v1/share/{token}/")
    # Re-sharing gives the same link.
    assert api.post(f"/api/v1/rides/{ride.id}/share/").json()["token"] == token

    public = APIClient().get(f"/api/v1/share/{token}/")
    assert public.status_code == 200
    body = public.json()
    assert body["status"] == "ACCEPTED" and body["captain"]["name"] == "Ravi"
    assert "start_pin" not in body and "phone" not in str(body)

    assert api.delete(f"/api/v1/rides/{ride.id}/share/").status_code == 204
    assert APIClient().get(f"/api/v1/share/{token}/").status_code == 404


def test_shared_link_stops_working_after_the_grace_period(customer, captain, clock):
    ride = services.create_ride(customer, ride_data())
    token = services.share_trip(customer, ride.id).token
    services.customer_cancel(customer, ride.id)
    assert APIClient().get(f"/api/v1/share/{token}/").status_code == 200
    clock.advance(minutes=31)
    assert APIClient().get(f"/api/v1/share/{token}/").status_code == 404


def test_only_active_rides_can_be_shared(customer, captain):
    ride = services.create_ride(customer, ride_data())
    services.customer_cancel(customer, ride.id)
    assert client_for(customer).post(f"/api/v1/rides/{ride.id}/share/").status_code == 409
