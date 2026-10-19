import json

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import DomainError
from apps.payments.models import Payment
from apps.payments.providers import get_provider
from apps.payments.serializers import PaymentSerializer
from apps.payments.services import handle_webhook_event

SIGNATURE_HEADER = "HTTP_X_PAYMENT_SIGNATURE"


class PaymentWebhookView(APIView):
    """Gateway callback. Authenticated by HMAC signature, not by user login."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        provider = get_provider()
        if not provider.verify_webhook(request.body, request.META.get(SIGNATURE_HEADER, "")):
            return Response({"detail": "Invalid signature."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            event = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            raise DomainError("Malformed payload.", code="malformed")
        handle_webhook_event(event)
        return Response({"status": "ok"})


class PaymentDetailView(APIView):
    """The owner polls this to see status. It never activates anything."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk, user=request.user)
        return Response(PaymentSerializer(payment).data)
