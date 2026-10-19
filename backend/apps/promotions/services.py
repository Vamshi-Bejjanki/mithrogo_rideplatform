"""Promo codes and referrals. The discount is always computed here, never taken from the client.

Who funds a discount: the platform. The captain's earnings stay on the full fare. For cash rides the
rider pays the captain the discounted amount, so the discount is credited to the captain's wallet.
"""

import secrets
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from core.exceptions import Conflict, DomainError
from core.models import PlatformConfig
from apps.notifications.services import notify
from apps.promotions.models import DiscountType, PromoCode, PromoRedemption, RedemptionStatus

CENT = Decimal("0.01")
_LIVE = [RedemptionStatus.RESERVED, RedemptionStatus.APPLIED]


def _has_completed_ride(user):
    from apps.rides.models import Ride, RideStatus

    return Ride.objects.filter(customer=user, status=RideStatus.COMPLETED).exists()


def discount_for(promo, fare):
    if promo.discount_type == DiscountType.FLAT:
        discount = promo.value
    else:
        discount = fare * promo.value / Decimal("100")
        if promo.max_discount is not None:
            discount = min(discount, promo.max_discount)
    # Never more than the fare: a ride is never free-plus-change.
    return min(discount, fare).quantize(CENT, ROUND_HALF_UP)


def validate(user, code, fare):
    """Return (promo, discount) for this rider and fare, or raise a DomainError saying why not."""
    promo = PromoCode.objects.filter(code=(code or "").strip().upper(), is_active=True).first()
    if promo is None:
        raise DomainError("This promo code is not valid.", code="promo_invalid")
    now = timezone.now()
    if promo.assigned_user_id and promo.assigned_user_id != user.id:
        raise DomainError("This promo code is not valid.", code="promo_invalid")
    if promo.valid_from and now < promo.valid_from:
        raise DomainError("This promo code is not active yet.", code="promo_not_started")
    if promo.valid_until and now > promo.valid_until:
        raise DomainError("This promo code has expired.", code="promo_expired")
    if fare < promo.min_fare:
        raise DomainError(f"This code needs a fare of at least ₹{promo.min_fare}.", code="promo_min_fare")
    if promo.first_ride_only and _has_completed_ride(user):
        raise DomainError("This code is for your first ride only.", code="promo_first_ride_only")

    live = PromoRedemption.objects.filter(promo=promo, status__in=_LIVE)
    if promo.max_uses_total is not None and live.count() >= promo.max_uses_total:
        raise DomainError("This promo code has been fully used.", code="promo_exhausted")
    if live.filter(user=user).count() >= promo.max_uses_per_user:
        raise DomainError("You have already used this promo code.", code="promo_already_used")
    return promo, discount_for(promo, fare)


def reserve(user, promo, ride, discount):
    """Hold the code for this ride. Called inside the ride-creation transaction."""
    return PromoRedemption.objects.create(promo=promo, user=user, ride=ride, discount=discount)


def on_ride_completed(ride):
    """Mark the code used, credit the captain for cash rides, and reward a referrer on a first ride."""
    redemption = PromoRedemption.objects.filter(ride=ride, status=RedemptionStatus.RESERVED).first()
    if redemption is not None:
        redemption.status = RedemptionStatus.APPLIED
        redemption.save(update_fields=["status", "updated_at"])
        from apps.rides.models import PaymentMethod

        if ride.payment_method == PaymentMethod.CASH and ride.discount_amount > 0 and ride.captain_id:
            from apps.wallets import services as wallet_services
            from apps.wallets.models import WalletTxnKind

            wallet_services.credit(ride.captain, ride.discount_amount, WalletTxnKind.PROMO_CREDIT, f"ride:{ride.id}")
    reward_referrer(ride.customer)


def release(ride):
    """A cancelled ride gives its code back."""
    PromoRedemption.objects.filter(ride=ride, status=RedemptionStatus.RESERVED).update(
        status=RedemptionStatus.RELEASED, updated_at=timezone.now()
    )


def available_for(user):
    """Codes a rider can see in the app: public active codes plus their own personal ones."""
    now = timezone.now()
    return (
        PromoCode.objects.filter(is_active=True)
        .filter(Q(assigned_user__isnull=True) | Q(assigned_user=user))
        .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=now))
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=now))
        .exclude(pk__in=PromoRedemption.objects.filter(user=user, status__in=_LIVE, promo__max_uses_per_user=1)
                 .values("promo_id"))
    )


# ---------- referrals ----------

def _new_code(prefix, length=6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O or 1/I, easy to read aloud
    return prefix + "".join(secrets.choice(alphabet) for _ in range(length))


def ensure_referral_code(profile):
    if profile.referral_code:
        return profile.referral_code
    for _ in range(10):
        profile.referral_code = _new_code("MG")
        try:
            with transaction.atomic():
                profile.save(update_fields=["referral_code", "updated_at"])
            return profile.referral_code
        except IntegrityError:
            continue
    raise RuntimeError("Could not generate a unique referral code.")


def _issue_reward(user, amount, reason):
    config = PlatformConfig.load()
    for _ in range(10):
        try:
            with transaction.atomic():
                promo = PromoCode.objects.create(
                    code=_new_code("RF", 8),
                    description=reason,
                    discount_type=DiscountType.FLAT,
                    value=amount,
                    max_uses_total=1,
                    max_uses_per_user=1,
                    assigned_user=user,
                    valid_until=timezone.now() + timedelta(days=config.referral_reward_valid_days),
                )
            break
        except IntegrityError:
            continue
    else:
        raise RuntimeError("Could not generate a unique reward code.")
    notify(user, "REFERRAL_REWARD", "You earned a ride discount", f"Use code {promo.code} for ₹{amount} off.",
           {"promo_code": promo.code})
    return promo


def apply_referral(user, code):
    """A new rider enters a friend's code. Once per rider, before their first completed ride."""
    from apps.customers.models import CustomerProfile
    from apps.customers.services import ensure_profile

    config = PlatformConfig.load()
    if config.referral_referee_reward <= 0 and config.referral_referrer_reward <= 0:
        raise DomainError("Referrals are not running right now.", code="referrals_off")

    with transaction.atomic():
        profile = CustomerProfile.objects.select_for_update().get(pk=ensure_profile(user).pk)
        if profile.referred_by_id:
            raise Conflict("You have already used a referral code.", code="referral_already_applied")
        if _has_completed_ride(user):
            raise Conflict("Referral codes are for new riders only.", code="referral_not_new")
        referrer = CustomerProfile.objects.filter(referral_code=(code or "").strip().upper()).select_related("user").first()
        if referrer is None or not referrer.user.is_active:
            raise DomainError("This referral code is not valid.", code="referral_invalid")
        if referrer.pk == profile.pk:
            raise DomainError("You cannot use your own referral code.", code="referral_self")
        profile.referred_by = referrer
        profile.save(update_fields=["referred_by", "updated_at"])

    reward = None
    if config.referral_referee_reward > 0:
        reward = _issue_reward(user, config.referral_referee_reward, "Welcome reward for joining with a referral")
    return reward


def reward_referrer(user):
    """Called when a rider completes a ride. Rewards their referrer once, on the first completed ride."""
    from apps.customers.models import CustomerProfile
    from apps.rides.models import Ride, RideStatus

    config = PlatformConfig.load()
    if config.referral_referrer_reward <= 0:
        return None
    with transaction.atomic():
        profile = CustomerProfile.objects.select_for_update().filter(user=user, referred_by__isnull=False).first()
        if profile is None or profile.referral_rewarded_at is not None:
            return None
        if Ride.objects.filter(customer=user, status=RideStatus.COMPLETED).count() != 1:
            return None
        profile.referral_rewarded_at = timezone.now()
        profile.save(update_fields=["referral_rewarded_at", "updated_at"])
        referrer = profile.referred_by.user
    return _issue_reward(referrer, config.referral_referrer_reward, "Thanks for referring a friend")


def referral_summary(user):
    from apps.customers.models import CustomerProfile
    from apps.customers.services import ensure_profile

    profile = ensure_profile(user)
    config = PlatformConfig.load()
    return {
        "referral_code": ensure_referral_code(profile),
        "referred_count": CustomerProfile.objects.filter(referred_by=profile).count(),
        "rewarded_count": CustomerProfile.objects.filter(referred_by=profile, referral_rewarded_at__isnull=False).count(),
        "applied_code": profile.referred_by.referral_code if profile.referred_by_id else None,
        "referee_reward": str(config.referral_referee_reward),
        "referrer_reward": str(config.referral_referrer_reward),
        "active": config.referral_referee_reward > 0 or config.referral_referrer_reward > 0,
    }
