import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string

from core.exceptions import DomainError, RateLimited
from apps.users.models import OtpChallenge

logger = logging.getLogger(__name__)


def _code_hash(phone, code):
    return hmac.new(settings.SECRET_KEY.encode(), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


def issue_otp(phone):
    """Create a fresh code, store only its hash, and send it. Returns the plain code (dev responses only)."""
    now = timezone.now()
    recent = OtpChallenge.objects.filter(phone=phone, created_at__gte=now - timedelta(hours=1)).count()
    if recent >= settings.OTP_MAX_SENDS_PER_HOUR:
        raise RateLimited("Too many codes requested. Try again later.", code="otp_rate_limited")

    code = "".join(secrets.choice("0123456789") for _ in range(settings.OTP_LENGTH))
    OtpChallenge.objects.create(
        phone=phone,
        code_hash=_code_hash(phone, code),
        expires_at=now + timedelta(seconds=settings.OTP_TTL_SECONDS),
    )
    try:
        provider = import_string(settings.SMS_PROVIDER)()
        provider.send_otp(phone, code, settings.OTP_TTL_SECONDS // 60)
    except Exception:
        # Do not leave a code behind that the user never received.
        OtpChallenge.objects.filter(phone=phone, code_hash=_code_hash(phone, code)).delete()
        logger.exception("SMS delivery failed for %s", phone)
        raise DomainError("We could not send the code. Please try again.", code="sms_failed")


def verify_otp(phone, code):
    """Check the code against the newest live challenge. Each wrong try counts against the attempt limit."""
    now = timezone.now()
    challenge = (
        OtpChallenge.objects.filter(phone=phone, consumed_at__isnull=True, expires_at__gt=now)
        .order_by("-created_at")
        .first()
    )
    if challenge is None:
        raise DomainError("Request a new code first.", code="otp_not_found")
    if challenge.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise RateLimited("Too many wrong attempts. Request a new code.", code="otp_locked")

    challenge.attempts += 1
    challenge.save(update_fields=["attempts"])
    if not hmac.compare_digest(challenge.code_hash, _code_hash(phone, code or "")):
        raise DomainError("The code is incorrect.", code="otp_invalid")

    challenge.consumed_at = now
    challenge.save(update_fields=["consumed_at"])
