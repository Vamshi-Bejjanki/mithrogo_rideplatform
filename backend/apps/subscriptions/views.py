from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.captains.services import describe_reasons, ensure_profile, todays_vehicle_type
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer
from apps.subscriptions import services
from apps.subscriptions.models import CaptainSubscription, PlatformDue, SubStatus
from apps.subscriptions.serializers import (
    CaptainSubscriptionSerializer,
    PlanCodeSerializer,
    PlatformDueSerializer,
    SubscriptionPlanSerializer,
    VerifyPaymentSerializer,
)
from apps.users.permissions import IsCaptain


class CaptainMixin:
    permission_classes = [IsCaptain]

    @property
    def captain(self):
        return ensure_profile(self.request.user)


class PlanListView(CaptainMixin, generics.ListAPIView):
    serializer_class = SubscriptionPlanSerializer

    def get_queryset(self):
        captain = self.captain
        chosen = todays_vehicle_type(captain)
        if chosen:
            return services.list_plans([chosen])
        verified = captain.vehicles.filter(is_verified=True).values_list("vehicle_type", flat=True)
        return services.list_plans(list(verified))


class SubscriptionSummaryView(CaptainMixin, APIView):
    def get(self, request):
        captain = self.captain
        current = services.active_subscription(captain) or (
            CaptainSubscription.objects.filter(captain=captain).select_related("plan").order_by("-created_at").first()
        )
        reasons = services.plan_block_reasons(captain)
        return Response(
            {
                "subscription": CaptainSubscriptionSerializer(current).data if current else None,
                "eligible": not reasons,
                "reasons": reasons,
                "message": describe_reasons(reasons),
                "pending_dues": services.pending_dues_total(captain),
                "today": services.todays_summary(captain),
            }
        )


class CreateDailyPaymentView(CaptainMixin, APIView):
    def post(self, request):
        serializer = PlanCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sub, payment = services.create_daily_subscription_payment(self.captain, serializer.validated_data["plan_code"])
        return Response(
            {"subscription_id": sub.id, "payment": PaymentSerializer(payment).data},
            status=status.HTTP_201_CREATED,
        )


class VerifyPaymentView(CaptainMixin, APIView):
    """Reports status only. Activation happens in the webhook, never because the app says 'paid'."""

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = get_object_or_404(Payment, pk=serializer.validated_data["payment_id"], user=request.user)
        sub = CaptainSubscription.objects.filter(payment=payment).select_related("plan").first()
        return Response(
            {
                "payment": PaymentSerializer(payment).data,
                "subscription": CaptainSubscriptionSerializer(sub).data if sub else None,
                "activated": bool(sub and sub.status == SubStatus.ACTIVE),
            }
        )


class SwitchToRideShareView(CaptainMixin, APIView):
    def post(self, request):
        serializer = PlanCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sub = services.switch_to_ride_share(self.captain, serializer.validated_data["plan_code"])
        return Response(CaptainSubscriptionSerializer(sub).data, status=status.HTTP_201_CREATED)


class SubscriptionHistoryView(CaptainMixin, generics.ListAPIView):
    serializer_class = CaptainSubscriptionSerializer

    def get_queryset(self):
        return (
            CaptainSubscription.objects.filter(captain=self.captain).select_related("plan").order_by("-created_at")
        )


class DuesView(CaptainMixin, APIView):
    def get(self, request):
        captain = self.captain
        dues = PlatformDue.objects.filter(captain=captain).order_by("-created_at")[:100]
        return Response(
            {
                "pending_total": services.pending_dues_total(captain),
                "items": PlatformDueSerializer(dues, many=True).data,
            }
        )


class PayDuesView(CaptainMixin, APIView):
    def post(self, request):
        payment = services.create_dues_payment(self.captain)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
