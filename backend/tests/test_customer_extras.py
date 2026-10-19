from decimal import Decimal

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from core.models import AuditLog, PlatformConfig
from apps.promotions.models import PromoCode, PromoRedemption, RedemptionStatus
from apps.rides import services
from apps.rides.models import Ride
from apps.users.models import Role, User
from apps.users.tokens import issue_tokens
from apps.wallets.services import get_wallet
from tests.helpers import make_user, ride_data, ride_payload

pytestmark = pytest.mark.django_db


def client_for(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def finish(captain, ride):
    services.accept_offer(captain, ride.id)
    services.mark_arrived(captain, ride.id)
    services.start_ride(captain, ride.id, pin=ride.start_pin)
    return services.complete_ride(captain, ride.id)


def set_config(**values):
    config = PlatformConfig.load()
    for key, value in values.items():
        setattr(config, key, value)
    config.save()


# ---------- promo codes ----------

def test_estimate_shows_the_discount(customer, captain):
    PromoCode.objects.create(code="flat20", discount_type="FLAT", value=Decimal("20"))
    body = client_for(customer).post(
        "/api/v1/rides/estimate/", {**ride_payload(), "promo_code": "FLAT20"}, format="json"
    ).json()
    assert body["discount"] == "20.00"
    assert Decimal(body["payable_fare"]) == Decimal(body["fare"]) - 20


def test_percent_promo_is_capped(customer, captain):
    PromoCode.objects.create(code="HALF", discount_type="PERCENT", value=Decimal("50"), max_discount=Decimal("10"))
    ride = services.create_ride(customer, {**ride_data(), "promo_code": "half"})
    assert ride.discount_amount == Decimal("10.00")
    assert ride.payable_fare == ride.estimated_fare - Decimal("10.00")


def test_invalid_and_expired_codes_are_rejected(customer, captain, clock):
    api = client_for(customer)
    bad = api.post("/api/v1/rides/estimate/", {**ride_payload(), "promo_code": "NOPE"}, format="json")
    assert bad.status_code == 400 and bad.json()["code"] == "promo_invalid"

    from datetime import timedelta

    PromoCode.objects.create(code="OLD", discount_type="FLAT", value=5, valid_until=clock.now - timedelta(days=1))
    old = api.post("/api/v1/rides/estimate/", {**ride_payload(), "promo_code": "OLD"}, format="json")
    assert old.json()["code"] == "promo_expired"


def test_code_is_used_once_and_given_back_on_cancel(customer, captain):
    PromoCode.objects.create(code="ONCE", discount_type="FLAT", value=5, max_uses_per_user=1)
    ride = services.create_ride(customer, {**ride_data(), "promo_code": "ONCE"})
    services.customer_cancel(customer, ride.id)
    assert PromoRedemption.objects.get(ride=ride).status == RedemptionStatus.RELEASED

    second = services.create_ride(customer, {**ride_data(), "promo_code": "ONCE"})
    finish(captain, second)
    assert PromoRedemption.objects.get(ride=second).status == RedemptionStatus.APPLIED
    with pytest.raises(Exception) as exc:
        services.create_ride(customer, {**ride_data(), "promo_code": "ONCE"})
    assert getattr(exc.value, "code", "") == "promo_already_used"


def test_cash_ride_discount_is_credited_to_the_captain(customer, captain):
    PromoCode.objects.create(code="CASH10", discount_type="FLAT", value=10)
    ride = services.create_ride(customer, {**ride_data(payment_method="CASH"), "promo_code": "CASH10"})
    finish(captain, ride)
    assert get_wallet(captain).balance == Decimal("10.00")


def test_online_ride_charges_the_discounted_fare(customer, captain):
    PromoCode.objects.create(code="ON10", discount_type="FLAT", value=10)
    ride = services.create_ride(customer, {**ride_data(), "promo_code": "ON10"})
    finish(captain, ride)
    payment = services.request_online_payment(customer, ride.id)
    assert payment.amount == Ride.objects.get(pk=ride.id).final_fare - 10


def test_first_ride_only_code(customer, captain):
    PromoCode.objects.create(code="FIRST", discount_type="FLAT", value=5, first_ride_only=True, max_uses_per_user=5)
    finish(captain, services.create_ride(customer, ride_data()))
    with pytest.raises(Exception) as exc:
        services.create_ride(customer, {**ride_data(), "promo_code": "FIRST"})
    assert exc.value.code == "promo_first_ride_only"


def test_promo_list_shows_public_and_personal_codes(customer):
    other = make_user(Role.CUSTOMER)
    PromoCode.objects.create(code="PUBLIC", discount_type="FLAT", value=5)
    PromoCode.objects.create(code="MINE", discount_type="FLAT", value=5, assigned_user=customer)
    PromoCode.objects.create(code="THEIRS", discount_type="FLAT", value=5, assigned_user=other)
    codes = {p["code"] for p in client_for(customer).get("/api/v1/customers/promos/").json()}
    assert codes == {"PUBLIC", "MINE"}


# ---------- referrals ----------

def test_referral_rewards_both_riders(customer, captain):
    set_config(referral_referee_reward=Decimal("30"), referral_referrer_reward=Decimal("50"))
    friend = make_user(Role.CUSTOMER, first_name="Friend")
    code = client_for(customer).get("/api/v1/customers/referral/").json()["referral_code"]
    assert code.startswith("MG")

    applied = client_for(friend).post("/api/v1/customers/referral/apply/", {"code": code.lower()}, format="json")
    assert applied.status_code == 201
    welcome = applied.json()["reward"]
    assert welcome["value"] == "30.00" and welcome["is_personal"] is True

    again = client_for(friend).post("/api/v1/customers/referral/apply/", {"code": code}, format="json")
    assert again.json()["code"] == "referral_already_applied"

    finish(captain, services.create_ride(friend, {**ride_data(), "promo_code": welcome["code"]}))
    reward = PromoCode.objects.get(assigned_user=customer)
    assert reward.value == Decimal("50")
    summary = client_for(customer).get("/api/v1/customers/referral/").json()
    assert summary["referred_count"] == 1 and summary["rewarded_count"] == 1


def test_referral_rules(customer, captain):
    set_config(referral_referee_reward=Decimal("30"))
    code = client_for(customer).get("/api/v1/customers/referral/").json()["referral_code"]
    own = client_for(customer).post("/api/v1/customers/referral/apply/", {"code": code}, format="json")
    assert own.json()["code"] == "referral_self"

    veteran = make_user(Role.CUSTOMER)
    finish(captain, services.create_ride(veteran, ride_data()))
    late = client_for(veteran).post("/api/v1/customers/referral/apply/", {"code": code}, format="json")
    assert late.json()["code"] == "referral_not_new"


def test_referrals_off_by_default(customer):
    friend = make_user(Role.CUSTOMER)
    code = client_for(customer).get("/api/v1/customers/referral/").json()["referral_code"]
    response = client_for(friend).post("/api/v1/customers/referral/apply/", {"code": code}, format="json")
    assert response.json()["code"] == "referrals_off"


# ---------- saved places ----------

def test_saved_places_crud_and_one_home(customer):
    api = client_for(customer)
    home = {"label": "HOME", "name": "Home", "address": "12 MG Road", "latitude": "18.672500", "longitude": "78.094000"}
    created = api.post("/api/v1/customers/places/", home, format="json")
    assert created.status_code == 201
    duplicate = api.post("/api/v1/customers/places/", home, format="json")
    assert duplicate.status_code == 409 and duplicate.json()["code"] == "place_exists"

    gym = {**home, "label": "OTHER", "name": "Gym"}
    assert api.post("/api/v1/customers/places/", gym, format="json").status_code == 201
    assert len(api.get("/api/v1/customers/places/").json()) == 2

    place_id = created.json()["id"]
    assert api.patch(f"/api/v1/customers/places/{place_id}/", {"name": "My home"}, format="json").json()["name"] == "My home"
    assert api.delete(f"/api/v1/customers/places/{place_id}/").status_code == 204

    other = make_user(Role.CUSTOMER)
    assert client_for(other).get(f"/api/v1/customers/places/{place_id}/").status_code == 404


# ---------- account deletion ----------

def test_delete_account_anonymises_and_frees_the_phone(customer, api):
    phone = customer.phone
    tokens = issue_tokens(customer)
    client = client_for(customer)
    assert client.get("/api/v1/auth/delete-account/").json() == {"can_delete": True, "reasons": []}

    refused = client.post("/api/v1/auth/delete-account/", {"confirm": False}, format="json")
    assert refused.status_code == 400
    assert client.post("/api/v1/auth/delete-account/", {"confirm": True}, format="json").status_code == 204

    customer.refresh_from_db()
    assert customer.is_active is False and customer.deleted_at is not None
    assert customer.phone != phone and customer.first_name == ""
    assert BlacklistedToken.objects.filter(token__user=customer).exists()
    assert AuditLog.objects.filter(action="account.deleted").exists()

    # The old refresh token no longer works.
    assert api.post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json").status_code == 401
    # The same number can sign up again as a brand-new account.
    from apps.users.services import login_for_role

    fresh = login_for_role(phone, Role.CUSTOMER)
    assert fresh.pk != customer.pk


def test_cannot_delete_during_a_ride(customer, captain):
    services.create_ride(customer, ride_data())
    client = client_for(customer)
    assert client.get("/api/v1/auth/delete-account/").json()["can_delete"] is False
    response = client.post("/api/v1/auth/delete-account/", {"confirm": True}, format="json")
    assert response.status_code == 409 and response.json()["code"] == "cannot_delete_active_ride"


def test_captain_with_wallet_money_cannot_delete(captain):
    from apps.wallets.models import WalletTxnKind
    from apps.wallets.services import credit

    captain.online_status = "OFFLINE"
    captain.save()
    credit(captain, Decimal("5"), WalletTxnKind.TOP_UP, "t1")
    response = client_for(captain.user).post("/api/v1/auth/delete-account/", {"confirm": True}, format="json")
    assert response.json()["code"] == "cannot_delete_wallet_balance"
    assert User.objects.get(pk=captain.user.pk).is_active
