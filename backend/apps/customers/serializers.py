from rest_framework import serializers

from apps.customers.models import CustomerProfile


class CustomerProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)
    first_name = serializers.CharField(source="user.first_name", max_length=80, allow_blank=True, required=False)
    last_name = serializers.CharField(source="user.last_name", max_length=80, allow_blank=True, required=False)
    email = serializers.EmailField(source="user.email", allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = CustomerProfile
        fields = [
            "phone",
            "first_name",
            "last_name",
            "email",
            "emergency_contact_name",
            "emergency_contact_phone",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_email(self, value):
        return value or None  # store NULL rather than an empty string (email is unique)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        if user_data:
            for field, value in user_data.items():
                setattr(instance.user, field, value)
            instance.user.save(update_fields=list(user_data.keys()) + ["updated_at"])
        return super().update(instance, validated_data)
