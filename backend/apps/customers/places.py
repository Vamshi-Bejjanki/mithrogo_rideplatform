from django.db import IntegrityError, transaction
from rest_framework import generics, serializers

from core.exceptions import Conflict, DomainError
from apps.customers.models import PlaceLabel, SavedPlace
from apps.users.permissions import IsCustomer

MAX_OTHER_PLACES = 20


class SavedPlaceSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-90, max_value=90)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-180, max_value=180)

    class Meta:
        model = SavedPlace
        fields = ["id", "label", "name", "address", "latitude", "longitude", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


def _save(serializer, **extra):
    try:
        with transaction.atomic():
            return serializer.save(**extra)
    except IntegrityError:
        label = serializer.validated_data.get("label", "")
        raise Conflict(f"You already have a saved {label.lower()} place. Edit that one instead.", code="place_exists")


class SavedPlaceListView(generics.ListCreateAPIView):
    """GET your saved places; POST one. One HOME and one WORK; up to 20 others."""

    serializer_class = SavedPlaceSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return SavedPlace.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        label = serializer.validated_data.get("label", PlaceLabel.OTHER)
        if label == PlaceLabel.OTHER and self.get_queryset().filter(label=PlaceLabel.OTHER).count() >= MAX_OTHER_PLACES:
            raise DomainError(f"You can save up to {MAX_OTHER_PLACES} places.", code="too_many_places")
        _save(serializer, user=self.request.user)


class SavedPlaceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavedPlaceSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return SavedPlace.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        _save(serializer)
