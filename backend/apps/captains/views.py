from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.captains.serializers import (
    CaptainProfileSerializer,
    KycDocumentSerializer,
    KycSubmitSerializer,
    LocationSerializer,
)
from apps.captains.services import (
    describe_reasons,
    eligibility_reasons,
    ensure_profile,
    go_offline,
    go_online,
    submit_kyc,
)
from apps.users.permissions import IsCaptain


class CaptainMixin:
    permission_classes = [IsCaptain]

    @property
    def captain(self):
        return ensure_profile(self.request.user)


class CaptainProfileView(CaptainMixin, generics.RetrieveUpdateAPIView):
    serializer_class = CaptainProfileSerializer

    def get_object(self):
        return self.captain


class CaptainStatusView(CaptainMixin, APIView):
    def get(self, request):
        captain = self.captain
        reasons = eligibility_reasons(captain)
        return Response(
            {
                "online_status": captain.online_status,
                "kyc_status": captain.kyc_status,
                "eligible": not reasons,
                "reasons": reasons,
                "message": describe_reasons(reasons),
            }
        )


class KycSubmitView(CaptainMixin, APIView):
    def post(self, request):
        serializer = KycSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        captain = submit_kyc(self.captain, serializer.validated_data)
        return Response(CaptainProfileSerializer(captain).data)


class KycDocumentView(CaptainMixin, generics.ListCreateAPIView):
    serializer_class = KycDocumentSerializer

    def get_queryset(self):
        return self.captain.kyc_documents.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(captain=self.captain)


class LocationView(CaptainMixin, APIView):
    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from apps.rides.services import record_captain_location

        record_captain_location(self.captain, data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OnlineView(CaptainMixin, APIView):
    def post(self, request):
        captain = go_online(self.captain)
        return Response(CaptainProfileSerializer(captain).data)


class OfflineView(CaptainMixin, APIView):
    def post(self, request):
        captain = go_offline(self.captain)
        return Response(CaptainProfileSerializer(captain).data)


class EarningsView(CaptainMixin, APIView):
    def get(self, request):
        from apps.rides.services import earnings_summary

        return Response(earnings_summary(self.captain))
