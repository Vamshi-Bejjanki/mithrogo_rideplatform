from decimal import Decimal

from django.db import migrations, models

# base_fare is now the flat fare for trips under 2 km; longer trips pay per km only.
RATES = {
    "BIKE": dict(base_fare="20.00", per_km="10.00", minimum_fare="20.00",
                 long_distance_after_km="15.00", long_distance_per_km="8.00"),
    "AUTO": dict(base_fare="30.00", per_km="15.00", minimum_fare="30.00",
                 long_distance_after_km="15.00", long_distance_per_km="12.00"),
}


def apply_rates(apps, schema_editor):
    FareConfig = apps.get_model("rides", "FareConfig")
    for vehicle_type, values in RATES.items():
        FareConfig.objects.filter(vehicle_type=vehicle_type).update(
            **{key: Decimal(value) for key, value in values.items()}
        )


class Migration(migrations.Migration):
    dependencies = [("rides", "0005_fare_long_distance_tier")]

    operations = [
        migrations.AlterField(
            model_name="fareconfig",
            name="base_fare",
            field=models.DecimalField(
                decimal_places=2, max_digits=8,
                help_text="Flat fare for trips under 2 km. Longer trips pay per km only.",
            ),
        ),
        migrations.RunPython(apply_rates, migrations.RunPython.noop),
    ]
