from django.urls import path

from apps.vehicles.views import CaptainVehicleListCreateView

urlpatterns = [
    path("", CaptainVehicleListCreateView.as_view(), name="captain-vehicles"),
]
