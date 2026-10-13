from django.urls import path

from apps.rides.views import (
    EstimateView,
    RideCancelView,
    RideDetailView,
    RideListCreateView,
    RidePaymentView,
    RideRatingView,
    RideTrackingView,
)

urlpatterns = [
    path("estimate/", EstimateView.as_view(), name="ride-estimate"),
    path("", RideListCreateView.as_view(), name="rides"),
    path("<uuid:pk>/", RideDetailView.as_view(), name="ride-detail"),
    path("<uuid:pk>/cancel/", RideCancelView.as_view(), name="ride-cancel"),
    path("<uuid:pk>/tracking/", RideTrackingView.as_view(), name="ride-tracking"),
    path("<uuid:pk>/payment/", RidePaymentView.as_view(), name="ride-payment"),
    path("<uuid:pk>/rating/", RideRatingView.as_view(), name="ride-rating"),
]
