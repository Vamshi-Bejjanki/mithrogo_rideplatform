from django.urls import path

from apps.rides.views import (
    EstimateView,
    OutstandingFeesView,
    RideCancelView,
    RideFeePaymentView,
    RideShareView,
    RideDetailView,
    RideListCreateView,
    RidePaymentView,
    RideRatingView,
    RideTrackingView,
)

urlpatterns = [
    path("estimate/", EstimateView.as_view(), name="ride-estimate"),
    path("", RideListCreateView.as_view(), name="rides"),
    path("outstanding-fees/", OutstandingFeesView.as_view(), name="ride-outstanding-fees"),
    path("<uuid:pk>/", RideDetailView.as_view(), name="ride-detail"),
    path("<uuid:pk>/cancel/", RideCancelView.as_view(), name="ride-cancel"),
    path("<uuid:pk>/tracking/", RideTrackingView.as_view(), name="ride-tracking"),
    path("<uuid:pk>/payment/", RidePaymentView.as_view(), name="ride-payment"),
    path("<uuid:pk>/rating/", RideRatingView.as_view(), name="ride-rating"),
    path("<uuid:pk>/fee-payment/", RideFeePaymentView.as_view(), name="ride-fee-payment"),
    path("<uuid:pk>/share/", RideShareView.as_view(), name="ride-share"),
]
