from rest_framework import serializers

from apps.users.models import Role, User
from apps.users.phone import normalize_phone


class PhoneField(serializers.CharField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        try:
            return normalize_phone(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class SendOtpSerializer(serializers.Serializer):
    phone = PhoneField(max_length=20)


class VerifyOtpSerializer(serializers.Serializer):
    phone = PhoneField(max_length=20)
    code = serializers.CharField(min_length=4, max_length=8)
    role = serializers.ChoiceField(choices=[Role.CUSTOMER, Role.CAPTAIN])


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "email", "first_name", "last_name", "role", "is_verified"]
        read_only_fields = fields
