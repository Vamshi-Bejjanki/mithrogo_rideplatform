from rest_framework import serializers

from apps.rides.models import PaymentMethod, Ride, RideOffer
from apps.vehicles.models import VehicleType


class CoordinatesMixin(serializers.Serializer):
    pickup_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-90, max_value=90)
    pickup_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-180, max_value=180)
    drop_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-90, max_value=90)
    drop_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-180, max_value=180)


class EstimateSerializer(CoordinatesMixin):
    vehicle_type = serializers.ChoiceField(choices=VehicleType.choices)


class RideCreateSerializer(EstimateSerializer):
    pickup_address = serializers.CharField(max_length=255)
    drop_address = serializers.CharField(max_length=255)
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices, default=PaymentMethod.ONLINE)


class RatingInputSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class RatingOutputSerializer(serializers.Serializer):
    rating = serializers.IntegerField()
    comment = serializers.CharField()


class RideSerializer(serializers.ModelSerializer):
    captain = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = [
            "id",
            "status",
            "vehicle_type",
            "pickup_address",
            "pickup_latitude",
            "pickup_longitude",
            "drop_address",
            "drop_latitude",
            "drop_longitude",
            "estimated_distance_km",
            "estimated_duration_minutes",
            "estimated_fare",
            "final_fare",
            "payment_method",
            "payment_status",
            "requested_at",
            "accepted_at",
            "arrived_at",
            "started_at",
            "completed_at",
            "cancelled_at",
            "cancellation_reason",
            "captain",
        ]
        read_only_fields = fields

    def get_captain(self, ride):
        if ride.captain_id is None:
            return None
        captain = ride.captain
        return {
            "name": captain.user.first_name or "Your captain",
            "rating": captain.rating,
            "total_rides": captain.total_rides,
        }


class CaptainRideSerializer(RideSerializer):
    customer_name = serializers.SerializerMethodField()

    class Meta(RideSerializer.Meta):
        fields = RideSerializer.Meta.fields + [
            "customer_name",
            "is_platform_ride",
            "share_reason",
            "platform_share_amount",
        ]
        read_only_fields = fields

    def get_customer_name(self, ride):
        return ride.customer.first_name or "Customer"


class OfferSerializer(serializers.ModelSerializer):
    ride_id = serializers.UUIDField(source="ride.id", read_only=True)
    pickup_address = serializers.CharField(source="ride.pickup_address", read_only=True)
    drop_address = serializers.CharField(source="ride.drop_address", read_only=True)
    fare = serializers.DecimalField(source="ride.estimated_fare", max_digits=10, decimal_places=2, read_only=True)
    vehicle_type = serializers.CharField(source="ride.vehicle_type", read_only=True)

    class Meta:
        model = RideOffer
        fields = [
            "ride_id",
            "sequence",
            "distance_km",
            "expires_at",
            "pickup_address",
            "drop_address",
            "fare",
            "vehicle_type",
        ]
        read_only_fields = fields
