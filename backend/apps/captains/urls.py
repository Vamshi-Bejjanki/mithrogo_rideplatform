from django.urls import path

from apps.captains.views import (
    CaptainProfileView,
    CaptainStatusView,
    EarningsView,
    KycDocumentView,
    KycSubmitView,
    LocationView,
    OfflineView,
    OnlineView,
)

urlpatterns = [
    path("profile/", CaptainProfileView.as_view(), name="captain-profile"),
    path("status/", CaptainStatusView.as_view(), name="captain-status"),
    path("status/online/", OnlineView.as_view(), name="captain-online"),
    path("status/offline/", OfflineView.as_view(), name="captain-offline"),
    path("kyc/", KycSubmitView.as_view(), name="captain-kyc"),
    path("kyc/documents/", KycDocumentView.as_view(), name="captain-kyc-documents"),
    path("location/", LocationView.as_view(), name="captain-location"),
    path("earnings/", EarningsView.as_view(), name="captain-earnings"),
]
