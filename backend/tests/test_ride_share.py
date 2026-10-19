from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.captains import services as captain_services
from apps.captains.models import OnlineStatus
from apps.captains.services import update_location
from apps.payments import services as payment_services
from apps.rides import services
from apps.rides.models import Ride, ShareReason
from apps.vehicles.models import VehicleType
from apps.subscriptions import services as subscription_services
from apps.subscriptions.models import DueStatus, DueType, PlatformDue, RideShareDay, SubStatus
from apps.users.models import Role
from core.exceptions import Conflict, Forbidden
from core.models import PlatformConfig
from tests.helpers import DROP, NEAR_PICKUP, captured_event, make_captain, make_user, ride_data, send_webhook


def run_ride(captain, rider, payment_method="CASH", drop=DROP):
    """Drive one ride through accept, arrive, start, and complete. Returns the refreshed ride."""
    update_location(captain, NEAR_PICKUP[0], NEAR_PICKUP[1])  # the captain app pings before taking a request
    ride = services.create_ride(rider, ride_data(payment_method=payment_method, drop=drop))
    services.accept_offer(captain, ride.id)
    services.mark_arrived(captain, ride.id)
    services.start_ride(captain, ride.id, pin=ride.start_pin)
    services.complete_ride(captain, ride.id)
    return Ride.objects.get(pk=ride.id)


def ride_share_captain():
    return make_captain(plan="ride_share", location=NEAR_PICKUP)


def platform_rides(captain):
    return Ride.objects.filter(captain=captain, is_platform_ride=True)


def settle_dues(captain):
    """Pay all pending dues through the gateway webhook, as a captain would."""
    payment = subscription_services.create_dues_payment(captain)
    send_webhook(APIClient(), captured_event(payment))


@pytest.fixture
def rider(db):
    return make_user(Role.CUSTOMER)


@pytest.mark.django_db
def test_fifth_completed_ride_is_taken_automatically(rider):
    captain = ride_share_captain()

    rides = [run_ride(captain, rider) for _ in range(5)]

    assert [r.is_platform_ride for r in rides] == [False, False, False, False, True]
    assert rides[4].share_reason == ShareReason.AUTO_5TH
    due = PlatformDue.objects.get(captain=captain, due_type=DueType.RIDE_SHARE)
    assert due.amount == rides[4].final_fare
    assert due.ride_id == rides[4].id


@pytest.mark.django_db
def test_rides_after_the_platform_ride_are_free_that_day(rider):
    captain = ride_share_captain()
    for _ in range(5):
        run_ride(captain, rider)

    extra = [run_ride(captain, rider) for _ in range(3)]

    assert not any(r.is_platform_ride for r in extra)
    assert platform_rides(captain).count() == 1
    assert PlatformDue.objects.filter(captain=captain, due_type=DueType.RIDE_SHARE).count() == 1


@pytest.mark.django_db
def test_surrendering_one_of_the_first_four_rides_takes_that_ride(rider):
    captain = ride_share_captain()
    run_ride(captain, rider)
    second = services.create_ride(rider, ride_data(payment_method="CASH"))
    services.accept_offer(captain, second.id)

    services.surrender(captain, second.id)
    services.mark_arrived(captain, second.id)
    services.start_ride(captain, second.id, pin=second.start_pin)
    services.complete_ride(captain, second.id)

    second.refresh_from_db()
    assert second.is_platform_ride
    assert second.share_reason == ShareReason.SURRENDERED
    later = [run_ride(captain, rider) for _ in range(4)]
    assert platform_rides(captain).count() == 1
    assert not any(r.is_platform_ride for r in later)


@pytest.mark.django_db
def test_only_one_surrender_per_day(rider):
    captain = ride_share_captain()
    first = services.create_ride(rider, ride_data(payment_method="CASH"))
    services.accept_offer(captain, first.id)
    services.surrender(captain, first.id)
    services.mark_arrived(captain, first.id)
    services.start_ride(captain, first.id, pin=first.start_pin)
    services.complete_ride(captain, first.id)
    second = services.create_ride(rider, ride_data(payment_method="CASH"))
    services.accept_offer(captain, second.id)

    with pytest.raises(Conflict) as info:
        services.surrender(captain, second.id)

    # Today's platform ride is already taken by the surrendered ride, so that is the reason reported.
    assert info.value.code == "platform_ride_taken"


@pytest.mark.django_db
def test_surrender_is_refused_once_four_rides_are_done(rider):
    captain = ride_share_captain()
    for _ in range(4):
        run_ride(captain, rider)
    fifth = services.create_ride(rider, ride_data(payment_method="CASH"))
    services.accept_offer(captain, fifth.id)

    with pytest.raises(Conflict) as info:
        services.surrender(captain, fifth.id)

    assert info.value.code == "surrender_window_closed"
    services.mark_arrived(captain, fifth.id)
    services.start_ride(captain, fifth.id, pin=fifth.start_pin)
    services.complete_ride(captain, fifth.id)
    fifth.refresh_from_db()
    assert fifth.share_reason == ShareReason.AUTO_5TH


@pytest.mark.django_db
def test_cancelled_rides_do_not_count_toward_the_five(rider):
    captain = ride_share_captain()
    for _ in range(3):
        ride = services.create_ride(rider, ride_data(payment_method="CASH"))
        services.accept_offer(captain, ride.id)
        services.cancel_ride(ride, actor=rider)
    for _ in range(4):
        run_ride(captain, rider)

    assert RideShareDay.objects.get(captain=captain).completed_rides == 4
    assert not platform_rides(captain).exists()


@pytest.mark.django_db
def test_cancelling_a_surrendered_ride_releases_the_surrender(rider):
    captain = ride_share_captain()
    ride = services.create_ride(rider, ride_data(payment_method="CASH"))
    services.accept_offer(captain, ride.id)
    services.surrender(captain, ride.id)

    services.cancel_ride(ride, actor=rider)

    assert RideShareDay.objects.get(captain=captain).surrendered_ride_id is None


@pytest.mark.django_db
def test_new_day_starts_a_fresh_count(clock, rider):
    captain = ride_share_captain()
    for _ in range(5):
        run_ride(captain, rider)

    clock.advance(days=1)
    captain_services.select_vehicle_for_today(captain, VehicleType.BIKE)
    day_two = [run_ride(captain, rider) for _ in range(5)]

    assert not any(r.is_platform_ride for r in day_two[:4])
    assert day_two[4].is_platform_ride
    assert platform_rides(captain).count() == 2


@pytest.mark.django_db
def test_shortfall_day_creates_fee_blocks_going_online_and_penalises_the_next_first_ride(clock, rider):
    captain = ride_share_captain()
    for _ in range(3):
        run_ride(captain, rider)

    clock.advance(days=1, hours=1)
    call_command("run_periodic_jobs")

    assert PlatformDue.objects.get(captain=captain, due_type=DueType.SHORTFALL_FEE).amount == Decimal("30.00")
    captain_services.go_offline(captain)
    with pytest.raises(Forbidden) as blocked:
        captain_services.go_online(captain)
    assert blocked.value.code == "shortfall_fee_unpaid"

    settle_dues(captain)
    captain_services.select_vehicle_for_today(captain, VehicleType.BIKE)
    captain_services.go_online(captain)
    penalty_ride = run_ride(captain, rider)
    assert penalty_ride.share_reason == ShareReason.PENALTY_FIRST_RIDE
    assert penalty_ride.is_platform_ride
    assert not run_ride(captain, rider).is_platform_ride


@pytest.mark.django_db
def test_zero_ride_day_has_no_penalty(clock):
    captain = ride_share_captain()

    clock.advance(days=2)
    call_command("run_periodic_jobs")
    captain_services.select_vehicle_for_today(captain, VehicleType.BIKE)

    assert not PlatformDue.objects.filter(captain=captain, due_type=DueType.SHORTFALL_FEE).exists()
    assert captain_services.eligibility_reasons(captain) == []


@pytest.mark.django_db
def test_day_with_a_platform_ride_is_not_a_shortfall(clock, rider):
    captain = ride_share_captain()
    for _ in range(5):
        run_ride(captain, rider)

    clock.advance(days=1)
    call_command("run_periodic_jobs")

    assert not PlatformDue.objects.filter(captain=captain, due_type=DueType.SHORTFALL_FEE).exists()


@pytest.mark.django_db
def test_dues_over_the_limit_block_going_online(rider):
    PlatformConfig.objects.update_or_create(pk=1, defaults={"unpaid_dues_limit": Decimal("10.00")})
    captain = ride_share_captain()
    for _ in range(5):
        run_ride(captain, rider, payment_method="CASH")

    captain.refresh_from_db()
    assert captain.online_status == OnlineStatus.OFFLINE
    with pytest.raises(Forbidden) as info:
        captain_services.go_online(captain)
    assert info.value.code == "dues_over_limit"


@pytest.mark.django_db
def test_online_paid_platform_ride_settles_its_due(api, rider):
    captain = ride_share_captain()
    for _ in range(4):
        run_ride(captain, rider)
    platform = run_ride(captain, rider, payment_method="ONLINE")
    assert platform.is_platform_ride

    payment = payment_services.create_payment(rider, "RIDE_PAYMENT", platform.final_fare, {"ride_id": str(platform.id)})
    send_webhook(api, captured_event(payment))

    assert PlatformDue.objects.get(ride=platform).status == DueStatus.SETTLED


@pytest.mark.django_db
def test_daily_plan_captain_is_not_counted_in_ride_share(rider):
    captain = make_captain(plan="daily", location=NEAR_PICKUP)

    for _ in range(5):
        run_ride(captain, rider)

    assert not RideShareDay.objects.filter(captain=captain).exists()
    assert not PlatformDue.objects.filter(captain=captain).exists()


@pytest.mark.django_db
def test_switching_to_daily_activates_only_after_payment(api, rider):
    captain = ride_share_captain()

    sub, payment = subscription_services.create_daily_subscription_payment(captain, "DAILY_BIKE")
    assert sub.status == SubStatus.PENDING
    assert subscription_services.active_subscription(captain).plan.plan_type == "RIDE_SHARE"

    send_webhook(api, captured_event(payment))

    assert subscription_services.active_subscription(captain).plan.plan_type == "DAILY_FLAT"


@pytest.mark.django_db
def test_plan_cannot_change_while_on_a_ride(rider):
    captain = make_captain(plan="daily", location=NEAR_PICKUP)
    ride = services.create_ride(rider, ride_data())
    services.accept_offer(captain, ride.id)

    with pytest.raises(Conflict) as info:
        subscription_services.switch_to_ride_share(captain, "RIDE_SHARE_BIKE")

    assert info.value.code == "ride_in_progress"
