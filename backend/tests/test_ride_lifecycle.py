from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.captains import services as captain_services
from apps.captains.models import CaptainProfile, OnlineStatus
from apps.rides import services
from apps.rides.models import Ride
from apps.users.models import Role
from core.exceptions import Conflict, Forbidden
from tests.helpers import NEAR_PICKUP, make_captain, make_user, ride_data, ride_payload, send_webhook


def as_client(user):
    """A separate client per user, so one user's session never leaks into another's requests."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_full_ride_flow_through_the_api(api, customer, captain):
    customer_api = as_client(customer)
    created = customer_api.post("/api/v1/rides/", ride_payload(), format="json")
    assert created.status_code == 201
    ride_id = created.json()["id"]
    assert created.json()["status"] == "SEARCHING"

    captain_api = as_client(captain.user)
    offers = captain_api.get("/api/v1/captains/offers/").json()
    assert offers[0]["ride_id"] == ride_id

    assert captain_api.post(f"/api/v1/captains/rides/{ride_id}/accept/").json()["status"] == "ACCEPTED"
    assert customer_api.get(f"/api/v1/rides/{ride_id}/tracking/").json()["captain"] is not None
    assert captain_api.post(f"/api/v1/captains/rides/{ride_id}/arrived/").json()["status"] == "CAPTAIN_ARRIVED"
    assert captain_api.post(f"/api/v1/captains/rides/{ride_id}/start/").json()["status"] == "STARTED"
    completed = captain_api.post(f"/api/v1/captains/rides/{ride_id}/complete/").json()
    assert completed["status"] == "COMPLETED"

    payment = customer_api.post(f"/api/v1/rides/{ride_id}/payment/", format="json")
    assert payment.status_code == 201
    webhook = send_webhook(api, captured_event_from_order(payment.json()))
    assert webhook.status_code == 200
    assert customer_api.get(f"/api/v1/rides/{ride_id}/").json()["payment_status"] == "PAID"

    rating = customer_api.post(f"/api/v1/rides/{ride_id}/rating/", {"rating": 5, "comment": "Great"}, format="json")
    assert rating.status_code == 201

    history = customer_api.get("/api/v1/rides/").json()
    assert [item["id"] for item in history] == [ride_id]
    earnings = captain_api.get("/api/v1/captains/earnings/").json()
    assert earnings["completed_rides"] == 1
    assert Decimal(earnings["net_earnings"]) == Decimal(completed["final_fare"])


def captured_event_from_order(payment_json):
    return {
        "event": "payment.captured",
        "provider_order_id": payment_json["provider_order_id"],
        "provider_payment_id": "pay_api_flow_1",
        "amount": payment_json["amount"],
    }


@pytest.mark.django_db
def test_final_fare_is_locked_at_request_time_and_ignores_client_values(api, customer, captain):
    payload = {**ride_payload(), "estimated_fare": "1.00", "final_fare": "1.00"}

    created = as_client(customer).post("/api/v1/rides/", payload, format="json")

    assert created.status_code == 201
    assert Decimal(created.json()["estimated_fare"]) > Decimal("1.00")
    assert created.json()["final_fare"] is None


@pytest.mark.django_db
def test_invalid_transitions_are_rejected():
    captain = make_captain(location=NEAR_PICKUP)
    customer = make_user(Role.CUSTOMER)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)

    with pytest.raises(Conflict) as skip_to_complete:
        services.complete_ride(captain, ride.id)
    with pytest.raises(Conflict) as skip_start:
        services.start_ride(captain, ride.id)

    assert skip_to_complete.value.code == "invalid_transition"
    assert skip_start.value.code == "invalid_transition"


@pytest.mark.django_db
def test_completed_ride_cannot_be_started_or_cancelled():
    captain = make_captain(location=NEAR_PICKUP)
    customer = make_user(Role.CUSTOMER)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    services.mark_arrived(captain, ride.id)
    services.start_ride(captain, ride.id)
    services.complete_ride(captain, ride.id)

    with pytest.raises(Conflict) as restart:
        services.start_ride(captain, ride.id)
    with pytest.raises(Conflict) as cancel:
        services.cancel_ride(ride, actor=customer)

    assert restart.value.code == "invalid_transition"
    assert cancel.value.code == "not_cancellable"


@pytest.mark.django_db
def test_cancelled_ride_cannot_be_completed():
    captain = make_captain(location=NEAR_PICKUP)
    customer = make_user(Role.CUSTOMER)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    services.cancel_ride(ride, actor=customer)

    with pytest.raises(Conflict) as info:
        services.complete_ride(captain, ride.id)

    assert info.value.code == "invalid_transition"


@pytest.mark.django_db
def test_customer_cancel_frees_the_captain_back_to_online():
    captain = make_captain(location=NEAR_PICKUP)
    customer = make_user(Role.CUSTOMER)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    captain.refresh_from_db()
    assert captain.online_status == OnlineStatus.BUSY

    services.cancel_ride(ride, actor=customer)

    captain.refresh_from_db()
    assert captain.online_status == OnlineStatus.ONLINE


@pytest.mark.django_db
def test_customer_cannot_cancel_a_started_ride():
    captain = make_captain(location=NEAR_PICKUP)
    customer = make_user(Role.CUSTOMER)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    services.mark_arrived(captain, ride.id)
    services.start_ride(captain, ride.id)

    with pytest.raises(Conflict) as info:
        services.cancel_ride(ride, actor=customer)

    assert info.value.code == "not_cancellable"


@pytest.mark.django_db
def test_customer_cannot_see_or_cancel_another_customers_ride(api):
    make_captain(location=NEAR_PICKUP)
    owner = make_user(Role.CUSTOMER)
    intruder = make_user(Role.CUSTOMER)
    ride = services.create_ride(owner, ride_data())

    seen = as_client(intruder).get(f"/api/v1/rides/{ride.id}/")
    cancelled = as_client(intruder).post(f"/api/v1/rides/{ride.id}/cancel/")

    assert seen.status_code == 404
    assert cancelled.status_code == 404


@pytest.mark.django_db
def test_captain_cannot_act_on_a_ride_assigned_to_someone_else():
    owner = make_captain(location=NEAR_PICKUP)
    other = make_captain(location=NEAR_PICKUP)
    customer = make_user(Role.CUSTOMER)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(owner, ride.id)

    with pytest.raises(Forbidden) as info:
        services.mark_arrived(other, ride.id)

    assert info.value.code == "not_your_ride"


@pytest.mark.django_db
def test_captain_location_is_shared_only_while_on_a_ride(api, customer):
    captain = make_captain(location=NEAR_PICKUP)
    ride = services.create_ride(customer, ride_data())
    customer_api = as_client(customer)

    before = customer_api.get(f"/api/v1/rides/{ride.id}/tracking/").json()
    services.accept_offer(captain, ride.id)
    during = customer_api.get(f"/api/v1/rides/{ride.id}/tracking/").json()

    assert before["captain"] is None
    assert during["captain"]["latitude"] is not None


@pytest.mark.django_db
def test_rating_needs_a_completed_ride_and_is_only_given_once(api, customer):
    captain = make_captain(location=NEAR_PICKUP)
    ride = services.create_ride(customer, ride_data())
    customer_api = as_client(customer)

    too_early = customer_api.post(f"/api/v1/rides/{ride.id}/rating/", {"rating": 4}, format="json")
    services.accept_offer(captain, ride.id)
    services.mark_arrived(captain, ride.id)
    services.start_ride(captain, ride.id)
    services.complete_ride(captain, ride.id)
    first = customer_api.post(f"/api/v1/rides/{ride.id}/rating/", {"rating": 4}, format="json")
    second = customer_api.post(f"/api/v1/rides/{ride.id}/rating/", {"rating": 2}, format="json")

    assert too_early.status_code == 409
    assert first.status_code == 201
    assert second.status_code == 409
    captain.refresh_from_db()
    assert captain.rating == Decimal("4.00")


@pytest.mark.django_db
def test_rating_must_be_between_one_and_five(api, customer):
    services.create_ride(customer, ride_data())
    ride = Ride.objects.get(customer=customer)

    response = as_client(customer).post(f"/api/v1/rides/{ride.id}/rating/", {"rating": 9}, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_cash_ride_is_collected_by_the_captain_not_paid_online(api, customer):
    captain = make_captain(location=NEAR_PICKUP)
    ride = services.create_ride(customer, ride_data(payment_method="CASH"))
    services.accept_offer(captain, ride.id)
    services.mark_arrived(captain, ride.id)
    services.start_ride(captain, ride.id)
    services.complete_ride(captain, ride.id)

    online_attempt = as_client(customer).post(f"/api/v1/rides/{ride.id}/payment/", format="json")
    collected = as_client(captain.user).post(f"/api/v1/captains/rides/{ride.id}/collect-cash/")

    assert online_attempt.status_code == 409
    assert online_attempt.json()["code"] == "cash_ride"
    assert collected.status_code == 200
    assert collected.json()["payment_status"] == "PAID"


@pytest.mark.django_db
def test_same_idempotency_key_over_the_api_returns_one_ride(api, customer):
    make_captain(location=NEAR_PICKUP)
    customer_api = as_client(customer)
    headers = {"HTTP_IDEMPOTENCY_KEY": "retry-key-1"}

    first = customer_api.post("/api/v1/rides/", ride_payload(), format="json", **headers)
    second = customer_api.post("/api/v1/rides/", ride_payload(), format="json", **headers)

    assert first.json()["id"] == second.json()["id"]


@pytest.mark.django_db
def test_captain_stays_offline_when_the_plan_blocks_them_after_a_ride():
    captain = make_captain(location=NEAR_PICKUP)
    customer = make_user(Role.CUSTOMER)
    ride = services.create_ride(customer, ride_data(payment_method="CASH"))
    services.accept_offer(captain, ride.id)
    services.mark_arrived(captain, ride.id)
    services.start_ride(captain, ride.id)
    CaptainProfile.objects.filter(pk=captain.pk).update(kyc_status="SUSPENDED")

    services.complete_ride(captain, ride.id)

    captain.refresh_from_db()
    assert captain.online_status == OnlineStatus.OFFLINE
    with pytest.raises(Forbidden):
        captain_services.go_online(captain)
