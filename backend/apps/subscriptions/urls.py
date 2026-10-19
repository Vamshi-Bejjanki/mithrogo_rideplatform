from django.urls import path

from apps.subscriptions.views import (
    CreateDailyPaymentView,
    DuesView,
    PayDuesView,
    PlanListView,
    SubscriptionHistoryView,
    SubscriptionSummaryView,
    SwitchToRideShareView,
    VerifyPaymentView,
)

urlpatterns = [
    path("", SubscriptionSummaryView.as_view(), name="captain-subscription"),
    path("plans/", PlanListView.as_view(), name="subscription-plans"),
    path("create-payment/", CreateDailyPaymentView.as_view(), name="subscription-create-payment"),
    path("verify-payment/", VerifyPaymentView.as_view(), name="subscription-verify-payment"),
    path("plan/", SwitchToRideShareView.as_view(), name="subscription-switch"),
    path("history/", SubscriptionHistoryView.as_view(), name="subscription-history"),
    path("dues/", DuesView.as_view(), name="captain-dues"),
    path("dues/pay/", PayDuesView.as_view(), name="captain-dues-pay"),
]
