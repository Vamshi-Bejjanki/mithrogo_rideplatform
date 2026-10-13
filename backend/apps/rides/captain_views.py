from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.captains.services import ensure_profile
from apps.rides import services
from apps.rides.models import Ride
from apps.rides.serializers import CaptainRideSerializer, OfferSerializer
from apps.users.permissions import IsCaptain


class CaptainMixin:
    permission_classes = [IsCaptain]

    @property
    def captain(self):
        return ensure_profile(self.request.user)


class OfferListView(CaptainMixin, generics.ListAPIView):
    serializer_class = OfferSerializer

    def get_queryset(self):
        return services.captain_offers(self.captain)


class CaptainRideListView(CaptainMixin, generics.ListAPIView):
    serializer_class = CaptainRideSerializer

    def get_queryset(self):
        queryset = Ride.objects.filter(captain=self.captain).select_related("customer", "captain__user")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset[:50]


class CaptainRideDetailView(CaptainMixin, generics.RetrieveAPIView):
    serializer_class = CaptainRideSerializer

    def get_object(self):
        return get_object_or_404(Ride, pk=self.kwargs["pk"], captain=self.captain)


class _RideActionView(CaptainMixin, APIView):
    def post(self, request, pk):
        ride = self.perform(self.captain, pk)
        return Response(CaptainRideSerializer(ride).data)

    def perform(self, captain, ride_id):
        raise NotImplementedError


class AcceptView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.accept_offer(captain, ride_id)


class RejectView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.reject_offer(captain, ride_id)


class ArrivedView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.mark_arrived(captain, ride_id)


class StartView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.start_ride(captain, ride_id)


class CompleteView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.complete_ride(captain, ride_id)


class SurrenderView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.surrender(captain, ride_id)


class CollectCashView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.collect_cash(captain, ride_id)
