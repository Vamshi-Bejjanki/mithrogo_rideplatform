from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.promotions import services
from apps.promotions.models import PromoCode
from apps.users.permissions import IsCustomer


class PromoCodeSerializer(serializers.ModelSerializer):
    is_personal = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = [
            "code",
            "description",
            "discount_type",
            "value",
            "max_discount",
            "min_fare",
            "valid_until",
            "first_ride_only",
            "is_personal",
        ]
        read_only_fields = fields

    def get_is_personal(self, promo):
        return promo.assigned_user_id is not None


class AvailablePromosView(generics.ListAPIView):
    """Codes this rider can use: public ones and their personal rewards."""

    serializer_class = PromoCodeSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return services.available_for(self.request.user)[:50]


class ReferralView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        return Response(services.referral_summary(request.user))


class ApplyReferralSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=12)


class ApplyReferralView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = ApplyReferralSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reward = services.apply_referral(request.user, serializer.validated_data["code"])
        return Response(
            {
                "detail": "Referral code applied.",
                "reward": PromoCodeSerializer(reward).data if reward else None,
            },
            status=status.HTTP_201_CREATED,
        )
