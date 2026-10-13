from decimal import Decimal

from django.db import migrations


def seed_plans(apps, schema_editor):
    """Starting values from the design doc. Admins change amounts afterwards; nothing is hard-coded in code."""
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    SubscriptionPlan.objects.get_or_create(
        code="DAILY_30",
        defaults={
            "name": "Daily plan",
            "plan_type": "DAILY_FLAT",
            "amount": Decimal("30.00"),
            "duration_days": 1,
            "is_active": True,
        },
    )
    SubscriptionPlan.objects.get_or_create(
        code="RIDE_SHARE_1_IN_5",
        defaults={
            "name": "Ride share (1 in 5)",
            "plan_type": "RIDE_SHARE",
            "amount": Decimal("0.00"),
            "qualifying_rides": 5,
            "shortfall_fee": Decimal("30.00"),
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0001_initial")]

    operations = [migrations.RunPython(seed_plans, migrations.RunPython.noop)]
