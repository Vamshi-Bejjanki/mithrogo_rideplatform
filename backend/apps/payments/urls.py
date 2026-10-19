from django.urls import path

from apps.payments.views import PaymentDetailView, PaymentWebhookView

urlpatterns = [
    path("webhook/", PaymentWebhookView.as_view(), name="payment-webhook"),
    path("<uuid:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
]
