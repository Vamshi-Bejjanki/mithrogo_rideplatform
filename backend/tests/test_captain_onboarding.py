from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.captains import services as captain_services
from apps.captains.models import KycStatus, OnlineStatus
from apps.captains.services import ensure_profile
from apps.subscriptions import services as subscription_services
from apps.users.models import Role
from apps.vehicles.models import Vehicle, VehicleType
from core.exceptions import Conflict, DomainError, Forbidden
from tests.helpers import make_captain, make_user


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def pending_captain():
    """Signed-up captain: no KYC, no vehicle, no plan."""
    user = make_user(Role.CAPTAIN)
    return ensure_profile(user), user


@pytest.mark.django_db
def test_kyc_submission_needs_a_document_first(as_user):
    _, user = pending_captain()

    response = as_user(user).post(
        "/api/v1/captains/kyc/",
        {"license_number": "TS0920100001234", "license_expiry": "2031-01-01"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["code"] == "documents_missing"


@pytest.mark.django_db
def test_kyc_document_upload_then_submit_moves_to_review(as_user, media):
    profile, user = pending_captain()
    api = as_user(user)
    upload = api.post(
        "/api/v1/captains/kyc/documents/",
        {
            "doc_type": "DRIVING_LICENSE",
            "file": SimpleUploadedFile("licence.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
        },
        format="multipart",
    )
    submit = api.post(
        "/api/v1/captains/kyc/",
        {"license_number": "TS0920100001234", "license_expiry": "2031-01-01"},
        format="json",
    )

    assert upload.status_code == 201
    assert submit.status_code == 200
    profile.refresh_from_db()
    assert profile.kyc_status == KycStatus.UNDER_REVIEW


@pytest.mark.django_db
def test_approved_kyc_is_locked_against_changes(as_user, media):
    profile = make_captain(plan=None, location=None, online=False)
    api = as_user(profile.user)

    response = api.post(
        "/api/v1/captains/kyc/",
        {"license_number": "NEW", "license_expiry": "2032-01-01"},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["code"] == "kyc_locked"


@pytest.mark.django_db
def test_captain_cannot_go_online_without_approved_kyc(as_user):
    profile = make_captain(approved=False, plan="daily", location=None, online=False)

    with pytest.raises(Forbidden) as info:
        captain_services.go_online(profile)

    assert info.value.code == "kyc_not_approved"


@pytest.mark.django_db
def test_captain_cannot_go_online_without_a_verified_vehicle():
    profile = make_captain(plan=None, verified=False, location=None, online=False)

    with pytest.raises(Forbidden) as info:
        captain_services.go_online(profile)

    assert info.value.code == "no_verified_vehicle"


@pytest.mark.django_db
def test_captain_cannot_go_online_without_a_plan():
    profile = make_captain(plan=None, location=None, online=False)

    with pytest.raises(Forbidden) as info:
        captain_services.go_online(profile)

    assert info.value.code == "no_active_plan"


@pytest.mark.django_db
def test_daily_plan_expires_and_blocks_going_online(clock):
    profile = make_captain(plan="daily", location=None, online=False)
    captain_services.go_offline(profile)

    clock.advance(hours=12, minutes=1)

    with pytest.raises(Forbidden) as info:
        captain_services.go_online(profile)
    assert info.value.code == "plan_expired"


@pytest.mark.django_db
def test_daily_plan_is_still_active_before_12_hours(clock):
    profile = make_captain(plan="daily", online=False)

    clock.advance(hours=11)
    captain_services.select_vehicle_for_today(profile, VehicleType.BIKE)
    captain_services.go_online(profile)


@pytest.mark.django_db
def test_daily_session_only_lets_its_vehicle_type_take_rides():
    profile = make_captain(plan="daily", vehicle_type=VehicleType.BIKE, location=None, online=False)
    Vehicle.objects.create(
        captain=profile,
        vehicle_type=VehicleType.AUTO,
        registration_number="TSAUTO1",
        make="Bajaj",
        model="RE",
        color="Yellow",
        is_verified=True,
    )

    assert captain_services.eligibility_reasons(profile) == []
    assert captain_services.eligibility_reasons(profile, VehicleType.AUTO) == ["vehicle_mismatch"]


@pytest.mark.django_db
def test_auto_daily_plan_costs_50_and_needs_a_verified_auto_vehicle():
    bike_captain = make_captain(plan=None, location=None, online=False)
    with pytest.raises(DomainError) as info:
        subscription_services.create_daily_subscription_payment(bike_captain, "DAILY_AUTO")
    assert info.value.code == "no_verified_vehicle"

    auto_captain = make_captain(plan=None, vehicle_type=VehicleType.AUTO, location=None, online=False)
    _, payment = subscription_services.create_daily_subscription_payment(auto_captain, "DAILY_AUTO")
    assert payment.amount == Decimal("50.00")


@pytest.mark.django_db
def test_daily_plan_cannot_be_bought_twice_while_active():
    profile = make_captain(plan="daily", location=None, online=False)

    with pytest.raises(Conflict) as info:
        subscription_services.create_daily_subscription_payment(profile, "DAILY_BIKE")

    assert info.value.code == "plan_already_active"


@pytest.mark.django_db
def test_suspended_captain_is_offline_and_blocked_until_reactivated():
    profile = make_captain()

    captain_services.suspend_captain(profile)
    profile.refresh_from_db()
    assert profile.kyc_status == KycStatus.SUSPENDED
    assert profile.online_status == OnlineStatus.OFFLINE

    with pytest.raises(Forbidden):
        captain_services.go_online(profile)

    captain_services.reactivate_captain(profile)
    profile.refresh_from_db()
    assert profile.kyc_status == KycStatus.APPROVED


@pytest.mark.django_db
def test_one_vehicle_per_type_and_unique_registration(as_user):
    profile = make_captain(plan=None, location=None, online=False)
    api = as_user(profile.user)
    api.post(
        "/api/v1/captains/vehicles/",
        {"vehicle_type": "AUTO", "registration_number": "TS09AA1111"},
        format="json",
    )

    same_type = api.post(
        "/api/v1/captains/vehicles/",
        {"vehicle_type": "AUTO", "registration_number": "TS09AA2222"},
        format="json",
    )
    same_plate = api.post(
        "/api/v1/captains/vehicles/",
        {"vehicle_type": "BIKE", "registration_number": "ts09aa1111"},
        format="json",
    )

    assert same_type.status_code == 409
    assert same_type.json()["code"] == "vehicle_type_taken"
    assert same_plate.status_code == 409
    assert same_plate.json()["code"] == "registration_taken"


@pytest.mark.django_db
def test_newly_added_vehicle_is_unverified_until_admin_approves(as_user):
    profile = make_captain(plan=None, location=None, online=False)
    api = as_user(profile.user)

    created = api.post(
        "/api/v1/captains/vehicles/",
        {"vehicle_type": "AUTO", "registration_number": "TS09BB3333"},
        format="json",
    )

    assert created.status_code == 201
    assert created.json()["is_verified"] is False
    assert not Vehicle.objects.get(registration_number="TS09BB3333").is_verified


@pytest.mark.django_db
def test_captain_must_choose_todays_vehicle_before_going_online(clock):
    profile = make_captain(plan="daily", location=None, online=False)
    captain_services.go_offline(profile)
    profile.day_vehicle_date = None
    profile.save(update_fields=["day_vehicle_date"])

    with pytest.raises(Forbidden) as info:
        captain_services.go_online(profile)
    assert info.value.code == "vehicle_not_selected"

    captain_services.select_vehicle_for_today(profile, VehicleType.BIKE)
    captain_services.go_online(profile)
