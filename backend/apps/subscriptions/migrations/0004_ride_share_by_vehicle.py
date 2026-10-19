from decimal import Decimal

from django.db import migrations


def split_ride_share_plans(apps, schema_editor):
    """Ride-share becomes one plan per vehicle: Bike shortfall ₹30, Auto ₹50.

    RIDE_SHARE_1_IN_5 is renamed rather than replaced, so existing subscriptions keep their plan.
    """
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    SubscriptionPlan.objects.filter(code="RIDE_SHARE_1_IN_5").update(
        code="RIDE_SHARE_BIKE",
        name="Bike ride share (1 in 5)",
        vehicle_type="BIKE",
        shortfall_fee=Decimal("30.00"),
    )
    SubscriptionPlan.objects.get_or_create(
        code="RIDE_SHARE_AUTO",
        defaults={
            "name": "Auto ride share (1 in 5)",
            "plan_type": "RIDE_SHARE",
            "amount": Decimal("0.00"),
            "vehicle_type": "AUTO",
            "qualifying_rides": 5,
            "shortfall_fee": Decimal("50.00"),
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0003_daily_plans_by_vehicle")]

    operations = [migrations.RunPython(split_ride_share_plans, migrations.RunPython.noop)]
