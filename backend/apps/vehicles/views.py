from rest_framework import generics, status
from rest_framework.response import Response

from apps.captains.services import ensure_profile
from apps.users.permissions import IsCaptain
from apps.vehicles.serializers import VehicleSerializer
from apps.vehicles.services import add_vehicle


class CaptainVehicleListCreateView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsCaptain]

    def get_queryset(self):
        return ensure_profile(self.request.user).vehicles.order_by("vehicle_type")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = add_vehicle(ensure_profile(request.user), serializer.validated_data)
        return Response(self.get_serializer(vehicle).data, status=status.HTTP_201_CREATED)
