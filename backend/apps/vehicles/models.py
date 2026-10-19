from django.db import models

from core.models import TimeStampedModel


class VehicleType(models.TextChoices):
    BIKE = "BIKE", "Bike"
    AUTO = "AUTO", "Auto"


class Vehicle(TimeStampedModel):
    captain = models.ForeignKey("captains.CaptainProfile", on_delete=models.CASCADE, related_name="vehicles")
    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices)
    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=60, blank=True)
    model = models.CharField(max_length=60, blank=True)
    color = models.CharField(max_length=30, blank=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["captain", "vehicle_type"], name="one_vehicle_per_type_per_captain"),
        ]

    def __str__(self):
        return f"{self.get_vehicle_type_display()} {self.registration_number}"
