import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

MSG91_OTP_URL = "https://api.msg91.com/api/v5/otp"


class SmsProvider:
    def send_otp(self, phone, code, ttl_minutes):
        raise NotImplementedError


class ConsoleSmsProvider(SmsProvider):
    """Development only: writes the code to the log. Refused when DEBUG is off (see settings)."""

    def send_otp(self, phone, code, ttl_minutes):
        logger.info("OTP for %s: %s (valid %s min)", phone, code, ttl_minutes)


class Msg91SmsProvider(SmsProvider):
    """Sends OTP SMS through MSG91's OTP API, using the DLT-approved template.

    Settings: MSG91_AUTH_KEY and MSG91_TEMPLATE_ID (from the MSG91 dashboard).
    Any failure raises, so a code is never reported as sent when MSG91 rejected it.
    """

    timeout_seconds = 10

    def send_otp(self, phone, code, ttl_minutes):
        if not settings.MSG91_AUTH_KEY or not settings.MSG91_TEMPLATE_ID:
            raise RuntimeError("MSG91 is not configured (MSG91_AUTH_KEY, MSG91_TEMPLATE_ID).")
        body = {
            "template_id": settings.MSG91_TEMPLATE_ID,
            "mobile": phone.lstrip("+"),  # MSG91 expects the number with country code and no plus sign
            "otp": code,
            "otp_expiry": ttl_minutes,
        }
        request = urllib.request.Request(
            MSG91_OTP_URL,
            data=json.dumps(body).encode(),
            headers={"authkey": settings.MSG91_AUTH_KEY, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"MSG91 returned HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"MSG91 unreachable: {exc}") from exc
        if payload.get("type") != "success":
            raise RuntimeError(f"MSG91 rejected the request: {payload.get('message', payload)}")
