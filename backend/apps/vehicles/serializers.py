from rest_framework import serializers

from apps.vehicles.models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ["id", "vehicle_type", "registration_number", "make", "model", "color", "is_verified"]
        read_only_fields = ["id", "is_verified"]
