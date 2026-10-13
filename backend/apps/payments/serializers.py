from rest_framework import serializers

from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "payment_type", "amount", "currency", "status", "provider_order_id", "created_at"]
        read_only_fields = fields
