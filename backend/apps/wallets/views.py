from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.captains.services import ensure_profile
from apps.payments.serializers import PaymentSerializer
from apps.subscriptions import services as subscription_services
from apps.subscriptions.serializers import CaptainSubscriptionSerializer, PlanCodeSerializer
from apps.users.permissions import IsCaptain
from apps.wallets import services
from apps.wallets.models import WalletTransaction
from apps.wallets.serializers import TopUpSerializer, WalletTransactionSerializer


class CaptainMixin:
    permission_classes = [IsCaptain]

    @property
    def captain(self):
        return ensure_profile(self.request.user)


class WalletView(CaptainMixin, APIView):
    def get(self, request):
        wallet = services.get_wallet(self.captain)
        recent = WalletTransaction.objects.filter(wallet=wallet)[:20]
        return Response({"balance": wallet.balance, "transactions": WalletTransactionSerializer(recent, many=True).data})


class WalletTopUpView(CaptainMixin, APIView):
    def post(self, request):
        serializer = TopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = services.start_top_up(self.captain, serializer.validated_data["amount"])
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class WalletPayPlanView(CaptainMixin, APIView):
    def post(self, request):
        serializer = PlanCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sub = subscription_services.pay_daily_plan_from_wallet(self.captain, serializer.validated_data["plan_code"])
        return Response(
            {"subscription": CaptainSubscriptionSerializer(sub).data, "balance": services.get_wallet(self.captain).balance},
            status=status.HTTP_201_CREATED,
        )


class WalletPayDuesView(CaptainMixin, APIView):
    def post(self, request):
        paid = subscription_services.pay_dues_from_wallet(self.captain)
        return Response({"paid": paid, "balance": services.get_wallet(self.captain).balance})
