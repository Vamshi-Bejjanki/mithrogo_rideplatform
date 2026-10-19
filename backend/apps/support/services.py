import logging

from django.db import transaction
from django.utils import timezone

from core.exceptions import Conflict
from apps.notifications.services import notify, notify_admins
from apps.rides.models import ACTIVE_STATUSES, Ride
from apps.support.models import SosAlert, SosStatus, SupportTicket, TicketCategory, TicketMessage, TicketStatus
from apps.users.models import Role

logger = logging.getLogger(__name__)


def owns_ride(user, ride):
    if user.role == Role.CUSTOMER:
        return ride.customer_id == user.id
    return ride.captain is not None and ride.captain.user_id == user.id


def ride_for(user, ride_id):
    if not ride_id:
        return None
    ride = Ride.objects.filter(pk=ride_id).select_related("captain").first()
    if ride is None or not owns_ride(user, ride):
        raise Conflict("That ride is not on your account.", code="ride_not_yours")
    return ride


def active_ride_for(user):
    if user.role == Role.CUSTOMER:
        return Ride.objects.filter(customer=user, status__in=ACTIVE_STATUSES).first()
    return Ride.objects.filter(captain__user=user, status__in=ACTIVE_STATUSES).first()


def add_message(ticket, author, body, is_staff):
    """Append to the conversation. A user reply reopens a resolved ticket; a staff reply notifies the user."""
    with transaction.atomic():
        ticket = SupportTicket.objects.select_for_update().get(pk=ticket.pk)
        if ticket.status == TicketStatus.CLOSED and not is_staff:
            raise Conflict("This ticket is closed. Please raise a new one.", code="ticket_closed")
        message = TicketMessage.objects.create(ticket=ticket, author=author, body=body, is_staff=is_staff)
        if is_staff and ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.IN_PROGRESS
        elif not is_staff and ticket.status == TicketStatus.RESOLVED:
            ticket.status = TicketStatus.OPEN
        ticket.save(update_fields=["status", "updated_at"])
    if is_staff:
        notify(ticket.user, "SUPPORT_REPLY", f"Reply on ticket #{ticket.pk}", body[:120], {"ticket_id": ticket.pk})
    return message


def set_ticket_status(ticket, status, note="", actor=None):
    ticket.status = status
    if note:
        ticket.resolution_note = note
    ticket.save(update_fields=["status", "resolution_note", "updated_at"])
    if status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
        notify(ticket.user, "TICKET_RESOLVED", f"Ticket #{ticket.pk} {ticket.get_status_display().lower()}",
               note[:120] if note else "", {"ticket_id": ticket.pk})
    return ticket


def raise_sos(user, ride_id=None, latitude=None, longitude=None, note=""):
    """Record an emergency, open a SAFETY ticket for follow-up, and alert every admin immediately."""
    ride = ride_for(user, ride_id) if ride_id else active_ride_for(user)
    with transaction.atomic():
        ticket = SupportTicket.objects.create(
            user=user,
            ride=ride,
            category=TicketCategory.SAFETY,
            description=f"SOS raised from the app. {note}".strip(),
        )
        alert = SosAlert.objects.create(
            user=user, ride=ride, ticket=ticket, latitude=latitude, longitude=longitude, note=note[:300]
        )
    logger.critical("SOS %s raised by user %s (ride %s)", alert.pk, user.pk, ride.pk if ride else None)
    who = user.full_name or user.phone
    notify_admins(
        "SOS_ALERT",
        "SOS: rider needs help" if user.role == Role.CUSTOMER else "SOS: captain needs help",
        f"{who} raised an SOS{' during a ride' if ride else ''}.",
        {"sos_id": alert.pk, "ride_id": str(ride.pk) if ride else ""},
    )
    return alert


def acknowledge_sos(alert, actor):
    if alert.status != SosStatus.OPEN:
        raise Conflict("This alert is already being handled.", code="sos_not_open")
    alert.status = SosStatus.ACKNOWLEDGED
    alert.handled_by = actor
    alert.acknowledged_at = timezone.now()
    alert.save(update_fields=["status", "handled_by", "acknowledged_at"])
    notify(alert.user, "SOS_ACKNOWLEDGED", "Help is on the way", "Our safety team has your alert and will contact you.",
           {"sos_id": alert.pk})
    return alert


def resolve_sos(alert, actor, note=""):
    if alert.status == SosStatus.RESOLVED:
        raise Conflict("This alert is already resolved.", code="sos_resolved")
    alert.status = SosStatus.RESOLVED
    alert.handled_by = alert.handled_by or actor
    alert.acknowledged_at = alert.acknowledged_at or timezone.now()
    alert.resolved_at = timezone.now()
    alert.resolution_note = note
    alert.save(update_fields=["status", "handled_by", "acknowledged_at", "resolved_at", "resolution_note"])
    if alert.ticket_id:
        set_ticket_status(alert.ticket, TicketStatus.RESOLVED, note, actor)
    return alert
