from django.utils import timezone

from core.exceptions import Conflict
from apps.rides.models import RideEvent, RideStatus

# Every allowed move. Anything else is rejected, no matter who asks.
ALLOWED_TRANSITIONS = {
    RideStatus.REQUESTED: {RideStatus.SEARCHING, RideStatus.CANCELLED},
    RideStatus.SEARCHING: {RideStatus.ACCEPTED, RideStatus.CANCELLED},
    RideStatus.ACCEPTED: {RideStatus.CAPTAIN_ARRIVED, RideStatus.CANCELLED},
    RideStatus.CAPTAIN_ARRIVED: {RideStatus.STARTED, RideStatus.CANCELLED},
    RideStatus.STARTED: {RideStatus.COMPLETED},
    RideStatus.COMPLETED: set(),
    RideStatus.CANCELLED: set(),
}

TIMESTAMP_FIELD = {
    RideStatus.ACCEPTED: "accepted_at",
    RideStatus.CAPTAIN_ARRIVED: "arrived_at",
    RideStatus.STARTED: "started_at",
    RideStatus.COMPLETED: "completed_at",
    RideStatus.CANCELLED: "cancelled_at",
}


def transition(ride, to_status, actor=None, note=""):
    """Move a ride to a new status. Validates the move, stamps the time, and writes the event log."""
    if to_status not in ALLOWED_TRANSITIONS.get(ride.status, set()):
        raise Conflict(f"A ride cannot move from {ride.status} to {to_status}.", code="invalid_transition")
    previous = ride.status
    ride.status = to_status
    fields = ["status", "updated_at"]
    timestamp_field = TIMESTAMP_FIELD.get(to_status)
    if timestamp_field:
        setattr(ride, timestamp_field, timezone.now())
        fields.append(timestamp_field)
    ride.save(update_fields=fields)
    RideEvent.objects.create(
        ride=ride,
        from_status=previous,
        to_status=to_status,
        actor=actor if actor is not None and getattr(actor, "is_authenticated", False) else None,
        note=note[:200],
    )
    return ride
