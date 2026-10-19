from django.urls import path

from apps.support.views import SosView, TicketDetailView, TicketListCreateView, TicketMessageView

urlpatterns = [
    path("tickets/", TicketListCreateView.as_view(), name="support-tickets"),
    path("tickets/<int:pk>/", TicketDetailView.as_view(), name="support-ticket-detail"),
    path("tickets/<int:pk>/messages/", TicketMessageView.as_view(), name="support-ticket-messages"),
    path("sos/", SosView.as_view(), name="support-sos"),
]
