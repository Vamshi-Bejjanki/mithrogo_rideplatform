from decimal import Decimal

from django.db import migrations


# Same rate for every vehicle: Rs 8/km, no base fare, no long-distance tier, and a Rs 20 minimum fare.
def apply_rates(apps, schema_editor):
    FareConfig = apps.get_model("rides", "FareConfig")
    FareConfig.objects.all().update(
        base_fare=Decimal("0.00"),
        per_km=Decimal("8.00"),
        minimum_fare=Decimal("20.00"),
        long_distance_after_km=None,
        long_distance_per_km=None,
    )


class Migration(migrations.Migration):
    dependencies = [("rides", "0006_fare_rapido_style_rates")]

    operations = [migrations.RunPython(apply_rates, migrations.RunPython.noop)]
