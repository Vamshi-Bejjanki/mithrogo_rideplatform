from decimal import Decimal

from django.db import migrations


def seed_fares(apps, schema_editor):
    """Starting fare rules for the pilot. Edit in admin; the pricing service reads these rows."""
    FareConfig = apps.get_model("rides", "FareConfig")
    FareConfig.objects.get_or_create(
        vehicle_type="BIKE",
        defaults={
            "base_fare": Decimal("20.00"),
            "per_km": Decimal("8.00"),
            "minimum_fare": Decimal("25.00"),
            "platform_customer_fee": Decimal("0.00"),
            "is_active": True,
        },
    )
    FareConfig.objects.get_or_create(
        vehicle_type="AUTO",
        defaults={
            "base_fare": Decimal("30.00"),
            "per_km": Decimal("14.00"),
            "minimum_fare": Decimal("40.00"),
            "platform_customer_fee": Decimal("0.00"),
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("rides", "0002_initial")]

    operations = [migrations.RunPython(seed_fares, migrations.RunPython.noop)]
