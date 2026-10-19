from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.captains.services import ensure_profile
from apps.rides import services
from apps.rides.models import Ride
from apps.rides.serializers import (
    CaptainCancelSerializer,
    CaptainRideSerializer,
    OfferSerializer,
    StartRideSerializer,
)
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


class StartView(CaptainMixin, APIView):
    """Body: {"pin": "1234"}, the rider's PIN, when ride start PINs are on."""

    def post(self, request, pk):
        serializer = StartRideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ride = services.start_ride(self.captain, pk, pin=serializer.validated_data["pin"])
        return Response(CaptainRideSerializer(ride).data)


class CaptainCancelView(CaptainMixin, APIView):
    def post(self, request, pk):
        serializer = CaptainCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ride = services.captain_cancel(self.captain, pk, data["reason"], data["note"])
        return Response(CaptainRideSerializer(ride).data)


class CompleteView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.complete_ride(captain, ride_id)


class SurrenderView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.surrender(captain, ride_id)


class CollectCashView(_RideActionView):
    def perform(self, captain, ride_id):
        return services.collect_cash(captain, ride_id)
