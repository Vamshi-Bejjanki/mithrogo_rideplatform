import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from core.exceptions import DomainError
from core.geo import haversine_km
from core.models import PlatformConfig
from apps.rides.models import FareConfig

CENT = Decimal("0.01")


@dataclass(frozen=True)
class Quote:
    vehicle_type: str
    distance_km: Decimal
    duration_minutes: int
    fare: Decimal


def _distance_charge(fare_config, distance):
    """Per-km charge; km beyond the long-distance threshold use the cheaper rate."""
    threshold, long_rate = fare_config.long_distance_after_km, fare_config.long_distance_per_km
    if threshold is None or long_rate is None or distance <= threshold:
        return fare_config.per_km * distance
    return fare_config.per_km * threshold + long_rate * (distance - threshold)


def quote(vehicle_type, pickup_latitude, pickup_longitude, drop_latitude, drop_longitude):
    """Estimate distance, duration, and fare from the database rules. The only place fares are computed."""
    config = PlatformConfig.load()
    fare_config = FareConfig.objects.filter(vehicle_type=vehicle_type, is_active=True).first()
    if fare_config is None:
        raise DomainError("This ride type is not available right now.", code="vehicle_unavailable")

    straight_km = haversine_km(pickup_latitude, pickup_longitude, drop_latitude, drop_longitude)
    distance = (Decimal(str(straight_km)) * config.road_distance_factor).quantize(CENT, ROUND_HALF_UP)
    if distance < config.min_trip_km:
        raise DomainError("Pickup and drop are too close to book a ride.", code="trip_too_short")

    minutes = max(1, math.ceil(float(distance) / float(config.average_speed_kmph) * 60))
    subtotal = fare_config.base_fare + _distance_charge(fare_config, distance)
    fare = (max(fare_config.minimum_fare, subtotal) + fare_config.platform_customer_fee).quantize(CENT, ROUND_HALF_UP)
    return Quote(vehicle_type=vehicle_type, distance_km=distance, duration_minutes=minutes, fare=fare)
