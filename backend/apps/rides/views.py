from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.serializers import PaymentSerializer
from apps.rides import services
from apps.rides.models import Ride
from apps.rides.serializers import (
    EstimateSerializer,
    RatingInputSerializer,
    RatingOutputSerializer,
    RideCreateSerializer,
    RideSerializer,
)
from apps.users.permissions import IsCustomer


class CustomerMixin:
    permission_classes = [IsCustomer]


class EstimateView(CustomerMixin, APIView):
    def post(self, request):
        serializer = EstimateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.estimate(serializer.validated_data))


class RideListCreateView(CustomerMixin, generics.ListAPIView):
    serializer_class = RideSerializer

    def get_queryset(self):
        return Ride.objects.filter(customer=self.request.user).select_related("captain__user")[:50]

    def post(self, request):
        serializer = RideCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = request.headers.get("Idempotency-Key", "").strip() or None
        ride = services.create_ride(request.user, serializer.validated_data, idempotency_key=key)
        return Response(RideSerializer(ride).data, status=status.HTTP_201_CREATED)


class RideDetailView(CustomerMixin, generics.RetrieveAPIView):
    serializer_class = RideSerializer

    def get_object(self):
        return services.get_customer_ride(self.request.user, self.kwargs["pk"])


class RideCancelView(CustomerMixin, APIView):
    def post(self, request, pk):
        ride = get_object_or_404(Ride, pk=pk, customer=request.user)
        ride = services.cancel_ride(ride, actor=request.user, reason="CANCELLED_BY_CUSTOMER")
        return Response(RideSerializer(ride).data)


class RideTrackingView(CustomerMixin, APIView):
    def get(self, request, pk):
        return Response(services.tracking(request.user, pk))


class RidePaymentView(CustomerMixin, APIView):
    def post(self, request, pk):
        payment = services.request_online_payment(request.user, pk)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class RideRatingView(CustomerMixin, APIView):
    def post(self, request, pk):
        serializer = RatingInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rating = services.rate_ride(request.user, pk, data["rating"], data["comment"])
        return Response(RatingOutputSerializer(rating).data, status=status.HTTP_201_CREATED)
