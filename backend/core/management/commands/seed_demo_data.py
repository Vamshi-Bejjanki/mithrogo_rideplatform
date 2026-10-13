from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

DEMO_CUSTOMERS = 3
DEMO_CAPTAINS = 3
# Near the default demo pickup point used in tests and the README.
DEMO_LOCATION = (Decimal("18.674000"), Decimal("78.095000"))


class Command(BaseCommand):
    """Development only: creates demo customers and captains. Safe to run more than once."""

    help = "Create demo customers and fully set-up captains for local testing."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo_data is only available with DJANGO_DEBUG on.")

        with transaction.atomic():
            customers = self._customers()
            captains = self._captains()
        self.stdout.write(f"Customers ready: {len(customers)}. Captains ready: {len(captains)}.")
        self.stdout.write("Customer phones: " + ", ".join(c.phone for c in customers))
        self.stdout.write("Captain phones: " + ", ".join(c.user.phone for c in captains))
        self.stdout.write("Log in with OTP (or the dev code printed in the server log).")

    def _customers(self):
        from apps.users.models import Role

        users = []
        for index in range(1, DEMO_CUSTOMERS + 1):
            phone = f"+9199000000{index:02d}"
            users.append(self._get_or_make(phone, lambda p=phone, i=index: self._new_user(Role.CUSTOMER, p, f"Demo{i}")))
        return users

    def _captains(self):
        from apps.captains.models import KycStatus
        from apps.captains.services import ensure_profile, update_location
        from apps.users.models import Role
        from apps.vehicles.models import Vehicle, VehicleType
        from apps.subscriptions import services as subscription_services
        from apps.payments import services as payment_services

        profiles = []
        for index in range(1, DEMO_CAPTAINS + 1):
            phone = f"+9199100000{index:02d}"
            user = self._get_or_make(phone, lambda p=phone, i=index: self._new_user(Role.CAPTAIN, p, f"Captain{i}"))
            profile = ensure_profile(user)
            if profile.kyc_status == KycStatus.APPROVED and profile.vehicles.exists():
                profiles.append(profile)
                continue
            profile.kyc_status = KycStatus.APPROVED
            profile.save(update_fields=["kyc_status", "updated_at"])
            Vehicle.objects.get_or_create(
                captain=profile,
                vehicle_type=VehicleType.BIKE if index % 2 else VehicleType.AUTO,
                defaults={
                    "registration_number": f"TSDEMO{index:04d}",
                    "make": "Bajaj",
                    "model": "RE",
                    "color": "Yellow",
                    "is_verified": True,
                },
            )
            if not profile.subscriptions.filter(status="ACTIVE").exists():
                sub, payment = subscription_services.create_daily_subscription_payment(profile, "DAILY_30")
                payment_services.mark_success(payment.provider_order_id, f"demo_pay_{payment.id.hex[:12]}", payment.amount)
            update_location(profile, DEMO_LOCATION[0], DEMO_LOCATION[1])
            profiles.append(profile)
        return profiles

    @staticmethod
    def _new_user(role, phone, first_name):
        from apps.customers.services import ensure_profile as ensure_customer_profile
        from apps.users.models import User

        user = User.objects.create_user(phone=phone, role=role, is_verified=True, first_name=first_name)
        if role == "CUSTOMER":
            ensure_customer_profile(user)
        return user

    @staticmethod
    def _get_or_make(phone, make):
        from apps.users.models import User

        existing = User.objects.filter(phone=phone).first()
        return existing if existing is not None else make()
