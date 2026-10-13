from django.urls import path

from apps.support.views import TicketListCreateView

urlpatterns = [
    path("tickets/", TicketListCreateView.as_view(), name="support-tickets"),
]
