from rest_framework import generics, serializers
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status

from core.exceptions import Conflict
from apps.rides.models import Ride
from apps.support.models import SupportTicket, TicketCategory
from apps.users.models import Role


class IsCustomerOrCaptain(BasePermission):
    message = "Support is available to customers and captains."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in (Role.CUSTOMER, Role.CAPTAIN))


class TicketSerializer(serializers.ModelSerializer):
    ride_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = SupportTicket
        fields = ["id", "category", "description", "ride_id", "status", "resolution_note", "created_at"]
        read_only_fields = ["id", "status", "resolution_note", "created_at"]

    def validate_category(self, value):
        if value not in TicketCategory.values:
            raise serializers.ValidationError("Unknown category.")
        return value


class TicketListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsCustomerOrCaptain]

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)[:50]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ride = None
        ride_id = data.pop("ride_id", None)
        if ride_id:
            ride = Ride.objects.filter(pk=ride_id).first()
            if ride is None or not self._owns_ride(request.user, ride):
                raise Conflict("That ride is not on your account.", code="ride_not_yours")
        ticket = SupportTicket.objects.create(user=request.user, ride=ride, **data)
        return Response(self.get_serializer(ticket).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _owns_ride(user, ride):
        if user.role == Role.CUSTOMER:
            return ride.customer_id == user.id
        return ride.captain is not None and ride.captain.user_id == user.id
