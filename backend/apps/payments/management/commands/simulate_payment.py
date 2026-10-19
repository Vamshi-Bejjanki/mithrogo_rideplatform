import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.payments.models import Payment
from apps.payments.providers import MockPaymentProvider
from apps.payments.services import handle_webhook_event


class Command(BaseCommand):
    """Development only: mark a mock payment as paid, through the same webhook path a real gateway uses."""

    help = "Simulate a successful gateway payment for a mock order."

    def add_arguments(self, parser):
        parser.add_argument("provider_order_id")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("simulate_payment is only available with DJANGO_DEBUG on.")
        payment = Payment.objects.filter(provider_order_id=options["provider_order_id"]).first()
        if payment is None:
            raise CommandError("No payment with that order id.")
        event = {
            "event": "payment.captured",
            "provider_order_id": payment.provider_order_id,
            "provider_payment_id": f"mock_pay_{payment.id.hex[:20]}",
            "amount": str(payment.amount),
        }
        body = json.dumps(event).encode()
        # Verify the signature the way the webhook view does, then apply the event.
        if not MockPaymentProvider().verify_webhook(body, MockPaymentProvider.sign(body)):
            raise CommandError("Signature check failed.")
        handle_webhook_event(event)
        self.stdout.write(f"Payment {payment.id} marked SUCCESS.")
