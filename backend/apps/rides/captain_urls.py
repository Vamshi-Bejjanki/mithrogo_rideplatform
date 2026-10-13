from django.urls import path

from apps.rides.captain_views import (
    AcceptView,
    ArrivedView,
    CaptainRideDetailView,
    CaptainRideListView,
    CollectCashView,
    CompleteView,
    OfferListView,
    RejectView,
    StartView,
    SurrenderView,
)

urlpatterns = [
    path("offers/", OfferListView.as_view(), name="captain-offers"),
    path("rides/", CaptainRideListView.as_view(), name="captain-rides"),
    path("rides/<uuid:pk>/", CaptainRideDetailView.as_view(), name="captain-ride-detail"),
    path("rides/<uuid:pk>/accept/", AcceptView.as_view(), name="captain-accept"),
    path("rides/<uuid:pk>/reject/", RejectView.as_view(), name="captain-reject"),
    path("rides/<uuid:pk>/arrived/", ArrivedView.as_view(), name="captain-arrived"),
    path("rides/<uuid:pk>/start/", StartView.as_view(), name="captain-start"),
    path("rides/<uuid:pk>/complete/", CompleteView.as_view(), name="captain-complete"),
    path("rides/<uuid:pk>/surrender/", SurrenderView.as_view(), name="captain-surrender"),
    path("rides/<uuid:pk>/collect-cash/", CollectCashView.as_view(), name="captain-collect-cash"),
]
