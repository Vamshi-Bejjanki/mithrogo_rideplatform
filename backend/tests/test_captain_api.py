from decimal import Decimal

import pytest

from apps.captains.models import CaptainProfile, OnlineStatus
from apps.captains.services import update_location
from apps.rides import services
from tests.helpers import NEAR_PICKUP, make_captain, make_user, ride_data
from apps.users.models import Role


@pytest.mark.django_db
def test_location_update_is_stored_and_returns_no_content(as_user):
    captain = make_captain(location=None, online=False)

    response = as_user(captain.user).post(
        "/api/v1/captains/location/",
        {"latitude": "18.674000", "longitude": "78.095000", "heading": "90", "speed": "12.5"},
        format="json",
    )

    assert response.status_code == 204
    captain.refresh_from_db()
    assert captain.current_latitude == Decimal("18.674000")
    assert captain.last_location_at is not None


@pytest.mark.django_db
def test_location_rejects_out_of_range_coordinates(as_user):
    captain = make_captain(location=None, online=False)

    response = as_user(captain.user).post(
        "/api/v1/captains/location/", {"latitude": "123", "longitude": "78"}, format="json"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_online_and_offline_endpoints_toggle_status(as_user):
    captain = make_captain(location=NEAR_PICKUP, online=False)
    api = as_user(captain.user)

    online = api.post("/api/v1/captains/status/online/")
    offline = api.post("/api/v1/captains/status/offline/")

    assert online.status_code == 200
    assert online.json()["online_status"] == OnlineStatus.ONLINE
    assert offline.json()["online_status"] == OnlineStatus.OFFLINE


@pytest.mark.django_db
def test_status_endpoint_explains_why_the_captain_cannot_go_online(as_user):
    captain = make_captain(approved=False, plan=None, location=None, online=False)

    response = as_user(captain.user).get("/api/v1/captains/status/")

    body = response.json()
    assert body["eligible"] is False
    assert "kyc_not_approved" in body["reasons"]
    assert "no_active_plan" in body["reasons"]
    assert body["message"]


@pytest.mark.django_db
def test_plans_list_shows_only_active_plans_with_database_values(as_user):
    captain = make_captain(plan=None, location=None, online=False)

    response = as_user(captain.user).get("/api/v1/captains/subscription/plans/")

    codes = {plan["code"]: plan for plan in response.json()}
    assert set(codes) == {"DAILY_BIKE", "RIDE_SHARE_BIKE"}  # bike captain sees bike plans only
    assert Decimal(codes["DAILY_BIKE"]["amount"]) == Decimal("30.00")
    assert codes["DAILY_BIKE"]["duration_hours"] == 12
    assert codes["RIDE_SHARE_BIKE"]["qualifying_rides"] == 5


@pytest.mark.django_db
def test_subscription_summary_shows_today_for_a_ride_share_captain(as_user):
    captain = make_captain(plan="ride_share", location=None, online=False)

    response = as_user(captain.user).get("/api/v1/captains/subscription/")

    body = response.json()
    assert body["subscription"]["plan"]["code"] == "RIDE_SHARE_BIKE"
    assert body["today"] == {
        "qualifying_rides": 5,
        "completed_rides": 0,
        "platform_ride_taken": False,
        "surrendered": False,
    }


@pytest.mark.django_db
def test_earnings_separate_fares_from_the_platform_share(as_user):
    captain = make_captain(plan="ride_share", location=NEAR_PICKUP)
    rider = make_user(Role.CUSTOMER)
    for _ in range(5):
        ride = services.create_ride(rider, ride_data(payment_method="CASH"))
        services.accept_offer(captain, ride.id)
        services.mark_arrived(captain, ride.id)
        services.start_ride(captain, ride.id, pin=ride.start_pin)
        services.complete_ride(captain, ride.id)
        update_location(captain, NEAR_PICKUP[0], NEAR_PICKUP[1])

    response = as_user(captain.user).get("/api/v1/captains/earnings/")

    body = response.json()
    assert body["completed_rides"] == 5
    fares = Decimal(body["fare_total"])
    platform = Decimal(body["platform_share"])
    assert platform > 0
    assert Decimal(body["net_earnings"]) == fares - platform
    assert CaptainProfile.objects.get(pk=captain.pk).total_rides == 5
