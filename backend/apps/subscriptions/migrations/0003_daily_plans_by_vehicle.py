from decimal import Decimal

from django.db import migrations, models


def set_daily_plans(apps, schema_editor):
    """Daily plans become 12-hour sessions priced by vehicle: Bike ₹30, Auto ₹50.

    DAILY_30 is renamed rather than replaced, so existing subscriptions keep their plan.
    """
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    SubscriptionPlan.objects.filter(code="DAILY_30").update(
        code="DAILY_BIKE",
        name="Bike daily plan",
        amount=Decimal("30.00"),
        duration_hours=12,
        vehicle_type="BIKE",
    )
    SubscriptionPlan.objects.get_or_create(
        code="DAILY_AUTO",
        defaults={
            "name": "Auto daily plan",
            "plan_type": "DAILY_FLAT",
            "amount": Decimal("50.00"),
            "duration_hours": 12,
            "vehicle_type": "AUTO",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0002_seed_plans")]

    operations = [
        migrations.RenameField(model_name="subscriptionplan", old_name="duration_days", new_name="duration_hours"),
        migrations.AlterField(
            model_name="subscriptionplan",
            name="duration_hours",
            field=models.PositiveIntegerField(
                blank=True, null=True, help_text="Daily plans only: how long one purchase lasts."
            ),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="vehicle_type",
            field=models.CharField(
                blank=True,
                choices=[("BIKE", "Bike"), ("AUTO", "Auto")],
                help_text="Daily plans only: the vehicle type this price applies to.",
                max_length=10,
                null=True,
            ),
        ),
        migrations.RunPython(set_daily_plans, migrations.RunPython.noop),
    ]
