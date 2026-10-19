from decimal import Decimal

from rest_framework import serializers

from apps.wallets.models import WalletTransaction


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ["id", "kind", "amount", "balance_after", "reference", "created_at"]
        read_only_fields = fields


class TopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("1"))
