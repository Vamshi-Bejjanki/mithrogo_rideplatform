from decimal import Decimal

import pytest

from apps.rides import pricing
from apps.rides.models import FareConfig
from apps.users.models import Role
from core.exceptions import DomainError
from tests.helpers import DROP, PICKUP, make_user, ride_payload

# About 0.45 km north of pickup: road estimate ~0.59 km, below the bike minimum fare.
SHORT_DROP = (Decimal("18.676550"), Decimal("78.094000"))
# About 0.2 km north: below the minimum trip length.
TOO_SHORT_DROP = (Decimal("18.674300"), Decimal("78.094000"))


def quote(vehicle_type="BIKE", drop=DROP):
    return pricing.quote(vehicle_type, PICKUP[0], PICKUP[1], drop[0], drop[1])


@pytest.mark.django_db
def test_bike_fare_is_base_plus_per_km_on_road_distance():
    result = quote()

    expected = max(Decimal("25.00"), Decimal("20.00") + Decimal("8.00") * result.distance_km)
    assert result.fare == expected.quantize(Decimal("0.01"))


@pytest.mark.django_db
def test_minimum_fare_applies_to_short_trips():
    result = quote(drop=SHORT_DROP)

    assert result.fare == Decimal("25.00")


@pytest.mark.django_db
def test_auto_uses_its_own_rates_and_minimum():
    result = quote("AUTO", drop=SHORT_DROP)

    assert result.fare == Decimal("40.00")


@pytest.mark.django_db
def test_customer_fee_is_added_on_top_of_the_fare():
    base = quote()
    FareConfig.objects.filter(vehicle_type="BIKE").update(platform_customer_fee=Decimal("5.00"))

    assert quote().fare == base.fare + Decimal("5.00")


@pytest.mark.django_db
def test_trips_below_minimum_distance_are_refused():
    with pytest.raises(DomainError) as info:
        quote(drop=TOO_SHORT_DROP)

    assert info.value.code == "trip_too_short"


@pytest.mark.django_db
def test_inactive_vehicle_type_is_not_available():
    FareConfig.objects.filter(vehicle_type="AUTO").update(is_active=False)

    with pytest.raises(DomainError) as info:
        quote("AUTO")

    assert info.value.code == "vehicle_unavailable"


@pytest.mark.django_db
def test_estimate_endpoint_returns_server_side_fare(api):
    customer = make_user(Role.CUSTOMER)
    api.force_authenticate(user=customer)
    payload = ride_payload()

    response = api.post("/api/v1/rides/estimate/", payload, format="json")

    assert response.status_code == 200
    body = response.json()
    assert Decimal(body["fare"]) == quote().fare
    assert body["currency"] == "INR"


@pytest.mark.django_db
def test_estimate_ignores_any_fare_sent_by_the_client(api):
    customer = make_user(Role.CUSTOMER)
    api.force_authenticate(user=customer)
    payload = {**ride_payload(), "fare": "1.00", "estimated_fare": "1.00"}

    response = api.post("/api/v1/rides/estimate/", payload, format="json")

    assert Decimal(response.json()["fare"]) == quote().fare
