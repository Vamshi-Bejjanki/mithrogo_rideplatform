from rest_framework import serializers

from apps.subscriptions.models import CaptainSubscription, PlatformDue, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "code",
            "name",
            "plan_type",
            "amount",
            "vehicle_type",
            "duration_hours",
            "qualifying_rides",
            "shortfall_fee",
        ]
        read_only_fields = fields


class CaptainSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = CaptainSubscription
        fields = ["id", "plan", "status", "start_at", "expires_at", "penalty_pending", "created_at"]
        read_only_fields = fields


class PlatformDueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformDue
        fields = ["id", "due_type", "amount", "status", "ride_id", "created_at", "settled_at"]
        read_only_fields = fields


class PlanCodeSerializer(serializers.Serializer):
    plan_code = serializers.CharField(max_length=40)


class VerifyPaymentSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
