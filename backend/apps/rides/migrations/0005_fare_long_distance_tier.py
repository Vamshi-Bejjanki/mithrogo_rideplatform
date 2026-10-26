from decimal import Decimal

from django.db import migrations, models

TIERS = {"BIKE": (Decimal("15.00"), Decimal("6.00")), "AUTO": (Decimal("15.00"), Decimal("11.00"))}


def seed_tiers(apps, schema_editor):
    FareConfig = apps.get_model("rides", "FareConfig")
    for vehicle_type, (after_km, rate) in TIERS.items():
        FareConfig.objects.filter(vehicle_type=vehicle_type).update(
            long_distance_after_km=after_km, long_distance_per_km=rate
        )


class Migration(migrations.Migration):
    dependencies = [("rides", "0004_ride_cancellation_fee_ride_cancellation_fee_status_and_more")]

    operations = [
        migrations.AddField(
            model_name="fareconfig",
            name="long_distance_after_km",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=6, null=True,
                help_text="Distance beyond this many km is charged at the long-distance rate. Empty = no tiering.",
            ),
        ),
        migrations.AddField(
            model_name="fareconfig",
            name="long_distance_per_km",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=8, null=True,
                help_text="Per-km rate for the distance beyond the threshold.",
            ),
        ),
        migrations.RunPython(seed_tiers, migrations.RunPython.noop),
    ]
