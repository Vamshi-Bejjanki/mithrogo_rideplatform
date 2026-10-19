from django.utils import timezone

from core.exceptions import Conflict
from apps.vehicles.models import Vehicle


def add_vehicle(captain, data):
    """Register a vehicle. It stays unverified until an admin verifies it. Captains cannot edit it afterwards."""
    registration = data["registration_number"].strip().upper()
    if Vehicle.objects.filter(registration_number=registration).exists():
        raise Conflict("This registration number is already in use.", code="registration_taken")
    if Vehicle.objects.filter(captain=captain, vehicle_type=data["vehicle_type"]).exists():
        raise Conflict("You already registered a vehicle of this type.", code="vehicle_type_taken")
    return Vehicle.objects.create(captain=captain, **{**data, "registration_number": registration})


def verify_vehicle(vehicle, actor=None):
    vehicle.is_verified = True
    vehicle.verified_at = timezone.now()
    vehicle.save(update_fields=["is_verified", "verified_at", "updated_at"])
    return vehicle


def unverify_vehicle(vehicle, actor=None):
    vehicle.is_verified = False
    vehicle.verified_at = None
    vehicle.save(update_fields=["is_verified", "verified_at", "updated_at"])
    return vehicle
