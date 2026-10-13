import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.exceptions import DomainError
from apps.payments.models import Payment, PaymentStatus, PaymentType
from apps.payments.providers import get_provider

logger = logging.getLogger(__name__)


def create_payment(user, payment_type, amount, metadata=None):
    """Create a payment order with the gateway. The amount always comes from the database, never from the client."""
    provider = get_provider()
    amount = Decimal(amount).quantize(Decimal("0.01"))
    order_id = provider.create_order(amount=amount, currency="INR", receipt=str(payment_type))
    return Payment.objects.create(
        user=user,
        payment_type=payment_type,
        amount=amount,
        currency="INR",
        provider=provider.name,
        provider_order_id=order_id,
        status=PaymentStatus.PENDING,
        metadata=metadata or {},
    )


def _dispatch_success(payment):
    """Apply the business effect of a successful payment. Imports are local to avoid import cycles."""
    from apps.rides import services as ride_services
    from apps.subscriptions import services as subscription_services

    if payment.payment_type == PaymentType.CAPTAIN_SUBSCRIPTION:
        subscription_services.on_subscription_paid(payment)
    elif payment.payment_type == PaymentType.DUES_SETTLEMENT:
        subscription_services.on_dues_paid(payment)
    elif payment.payment_type == PaymentType.RIDE_PAYMENT:
        ride_services.on_ride_paid(payment)


def mark_success(provider_order_id, provider_payment_id, amount):
    """Confirm a payment. Idempotent: a repeated webhook changes nothing.

    Only the gateway webhook calls this. The mobile app's 'success' never does.
    """
    with transaction.atomic():
        payment = Payment.objects.select_for_update().filter(provider_order_id=provider_order_id).first()
        if payment is None:
            raise DomainError("Unknown payment order.", code="unknown_order")
        if payment.status == PaymentStatus.SUCCESS:
            return payment
        if Decimal(str(amount)).quantize(Decimal("0.01")) != payment.amount:
            logger.error("Amount mismatch for order %s", provider_order_id)
            raise DomainError("The amount does not match the order.", code="amount_mismatch")
        payment.status = PaymentStatus.SUCCESS
        payment.provider_payment_id = provider_payment_id
        payment.updated_at = timezone.now()
        payment.save(update_fields=["status", "provider_payment_id", "updated_at"])
        _dispatch_success(payment)
    return payment


def mark_failed(provider_order_id):
    payment = Payment.objects.filter(provider_order_id=provider_order_id).first()
    if payment is not None and payment.status not in (PaymentStatus.SUCCESS, PaymentStatus.FAILED):
        payment.status = PaymentStatus.FAILED
        payment.save(update_fields=["status", "updated_at"])
    return payment


def handle_webhook_event(event):
    """Route a verified gateway event. Signature checking happens in the view before this is called."""
    kind = event.get("event")
    if kind == "payment.captured":
        return mark_success(event["provider_order_id"], event["provider_payment_id"], event["amount"])
    if kind == "payment.failed":
        return mark_failed(event["provider_order_id"])
    raise DomainError("Unsupported event.", code="unsupported_event")
