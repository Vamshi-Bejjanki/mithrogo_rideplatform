from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.exceptions import Conflict, DomainError, Forbidden
from apps.captains.models import CaptainProfile, KycStatus, OnlineStatus
from apps.notifications.services import notify

REASON_MESSAGES = {
    "account_suspended": "Your account is suspended.",
    "kyc_not_approved": "Your documents are not approved yet.",
    "no_verified_vehicle": "You need a verified vehicle.",
    "no_active_plan": "Choose a plan to start taking rides.",
    "plan_expired": "Your daily plan has expired. Renew to go online.",
    "shortfall_fee_unpaid": "Pay your shortfall fee to go online.",
    "dues_over_limit": "Your unpaid platform dues are over the limit. Pay them to go online.",
}


def ensure_profile(user):
    profile, _ = CaptainProfile.objects.get_or_create(user=user)
    return profile


def eligibility_reasons(captain, vehicle_type=None):
    """Every reason this captain cannot take rides right now (empty list = eligible).

    Used by go-online, matching, and accept. The single source of truth for eligibility.
    """
    from apps.subscriptions.services import plan_block_reasons

    reasons = []
    if not captain.user.is_active:
        reasons.append("account_suspended")
    if captain.kyc_status != KycStatus.APPROVED:
        reasons.append("kyc_not_approved")
    vehicles = captain.vehicles.filter(is_verified=True)
    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    if not vehicles.exists():
        reasons.append("no_verified_vehicle")
    reasons.extend(plan_block_reasons(captain))
    return reasons


def is_eligible(captain, vehicle_type=None):
    return not eligibility_reasons(captain, vehicle_type)


def describe_reasons(reasons):
    return " ".join(REASON_MESSAGES.get(reason, reason) for reason in reasons)


@transaction.atomic
def go_online(captain):
    captain = CaptainProfile.objects.select_for_update().get(pk=captain.pk)  # decide on current state, not a copy
    if captain.online_status == OnlineStatus.BUSY:
        raise Conflict("You are on a ride right now.", code="captain_busy")
    reasons = eligibility_reasons(captain)
    if reasons:
        raise Forbidden(describe_reasons(reasons), code=reasons[0])
    captain.online_status = OnlineStatus.ONLINE
    captain.save(update_fields=["online_status", "updated_at"])
    return captain


@transaction.atomic
def go_offline(captain):
    captain = CaptainProfile.objects.select_for_update().get(pk=captain.pk)
    if captain.online_status == OnlineStatus.BUSY:
        raise Conflict("Finish your current ride before going offline.", code="captain_busy")
    captain.online_status = OnlineStatus.OFFLINE
    captain.save(update_fields=["online_status", "updated_at"])
    return captain


def update_location(captain, latitude, longitude, heading=None, speed=None):
    captain.current_latitude = Decimal(str(latitude))
    captain.current_longitude = Decimal(str(longitude))
    captain.last_location_at = timezone.now()
    captain.save(update_fields=["current_latitude", "current_longitude", "last_location_at", "updated_at"])
    return captain


def submit_kyc(captain, data):
    """Captain sends licence details for review. Locked once approved or suspended."""
    if captain.kyc_status in (KycStatus.APPROVED, KycStatus.SUSPENDED):
        raise Conflict("Your documents are locked. Contact support to change them.", code="kyc_locked")
    if not captain.kyc_documents.exists():
        raise DomainError("Upload at least one document before submitting.", code="documents_missing")
    for field in ("license_number", "license_expiry", "date_of_birth", "address"):
        if field in data and data[field] not in (None, ""):
            setattr(captain, field, data[field])
    captain.kyc_status = KycStatus.UNDER_REVIEW
    captain.save()
    return captain


def approve_kyc(captain, actor=None):
    if captain.kyc_status == KycStatus.SUSPENDED:
        raise Conflict("Reactivate the captain before approving.", code="captain_suspended")
    captain.kyc_status = KycStatus.APPROVED
    captain.save(update_fields=["kyc_status", "updated_at"])
    notify(captain.user, "KYC_APPROVED", "Documents approved", "You can now choose a plan and go online.")
    return captain


def reject_kyc(captain, actor=None):
    if captain.online_status == OnlineStatus.BUSY:
        raise Conflict("The captain is on a ride.", code="captain_busy")
    captain.kyc_status = KycStatus.REJECTED
    captain.online_status = OnlineStatus.OFFLINE
    captain.save(update_fields=["kyc_status", "online_status", "updated_at"])
    notify(captain.user, "KYC_REJECTED", "Documents need changes", "Please review your documents and resubmit.")
    return captain


@transaction.atomic
def suspend_captain(captain, actor=None):
    captain = CaptainProfile.objects.select_for_update().get(pk=captain.pk)
    if captain.online_status == OnlineStatus.BUSY:
        raise Conflict("The captain is on a ride. Suspend after it ends.", code="captain_busy")
    captain.kyc_status = KycStatus.SUSPENDED
    captain.online_status = OnlineStatus.OFFLINE
    captain.save(update_fields=["kyc_status", "online_status", "updated_at"])
    notify(captain.user, "ACCOUNT_SUSPENDED", "Account suspended", "Contact support for details.")
    return captain


def reactivate_captain(captain, actor=None):
    if captain.kyc_status != KycStatus.SUSPENDED:
        raise Conflict("This captain is not suspended.", code="not_suspended")
    captain.kyc_status = KycStatus.APPROVED
    captain.save(update_fields=["kyc_status", "updated_at"])
    notify(captain.user, "ACCOUNT_REACTIVATED", "Account reactivated", "You can go online again.")
    return captain
