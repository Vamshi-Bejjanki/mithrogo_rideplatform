import hashlib
import hmac
import uuid

from django.conf import settings
from django.utils.module_loading import import_string


class PaymentProvider:
    """Gateway adapter. A real gateway (Razorpay, Cashfree, ...) implements the same two methods."""

    name = ""

    def create_order(self, *, amount, currency, receipt):
        raise NotImplementedError

    def verify_webhook(self, body, signature):
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    """Stands in for a real gateway during development and tests. Webhooks are HMAC-signed like the real thing."""

    name = "MOCK"

    def create_order(self, *, amount, currency, receipt):
        return f"mock_order_{uuid.uuid4().hex}"

    def verify_webhook(self, body, signature):
        return hmac.compare_digest(self.sign(body), signature or "")

    @staticmethod
    def sign(body):
        secret = settings.PAYMENT_WEBHOOK_SECRET
        if not secret:
            raise RuntimeError("PAYMENT_WEBHOOK_SECRET is not configured.")
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def get_provider():
    return import_string(settings.PAYMENT_PROVIDER)()
