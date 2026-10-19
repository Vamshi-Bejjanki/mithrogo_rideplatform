from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.support import services
from apps.support.models import SosAlert, SupportTicket, TicketCategory, TicketMessage
from apps.users.models import Role


class IsCustomerOrCaptain(BasePermission):
    message = "Support is available to customers and captains."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in (Role.CUSTOMER, Role.CAPTAIN))


class TicketMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketMessage
        fields = ["id", "is_staff", "author_name", "body", "created_at"]
        read_only_fields = fields

    def get_author_name(self, message):
        if message.is_staff:
            return "MithroGo Support"
        return message.author.first_name if message.author else ""


class TicketSerializer(serializers.ModelSerializer):
    ride_id = serializers.UUIDField(required=False, allow_null=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id", "category", "description", "ride_id", "status", "resolution_note",
            "message_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "resolution_note", "message_count", "created_at", "updated_at"]

    def validate_category(self, value):
        if value not in TicketCategory.values:
            raise serializers.ValidationError("Unknown category.")
        return value

    def get_message_count(self, ticket):
        return ticket.messages.count()


class TicketDetailSerializer(TicketSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta(TicketSerializer.Meta):
        fields = TicketSerializer.Meta.fields + ["messages"]
        read_only_fields = fields


class TicketListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsCustomerOrCaptain]

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)[:50]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ride = services.ride_for(request.user, data.pop("ride_id", None))
        ticket = SupportTicket.objects.create(user=request.user, ride=ride, **data)
        return Response(self.get_serializer(ticket).data, status=status.HTTP_201_CREATED)


class TicketDetailView(generics.RetrieveAPIView):
    serializer_class = TicketDetailSerializer
    permission_classes = [IsCustomerOrCaptain]

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user).prefetch_related("messages__author")


class MessageInputSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=2000)


class TicketMessageView(APIView):
    """GET the conversation; POST a reply."""

    permission_classes = [IsCustomerOrCaptain]

    def _ticket(self, request, pk):
        return get_object_or_404(SupportTicket, pk=pk, user=request.user)

    def get(self, request, pk):
        ticket = self._ticket(request, pk)
        return Response(TicketMessageSerializer(ticket.messages.select_related("author"), many=True).data)

    def post(self, request, pk):
        serializer = MessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = services.add_message(self._ticket(request, pk), request.user, serializer.validated_data["body"], False)
        return Response(TicketMessageSerializer(message).data, status=status.HTTP_201_CREATED)


class SosInputSerializer(serializers.Serializer):
    ride_id = serializers.UUIDField(required=False, allow_null=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True,
                                        min_value=-90, max_value=90)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True,
                                         min_value=-180, max_value=180)
    note = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")


class SosSerializer(serializers.ModelSerializer):
    ride_id = serializers.UUIDField(source="ride.id", read_only=True, default=None)
    ticket_id = serializers.IntegerField(source="ticket.id", read_only=True, default=None)

    class Meta:
        model = SosAlert
        fields = ["id", "status", "ride_id", "ticket_id", "latitude", "longitude", "note",
                  "acknowledged_at", "resolved_at", "created_at"]
        read_only_fields = fields


class SosView(APIView):
    """POST raises an SOS (the active ride is attached automatically). GET lists your recent alerts."""

    permission_classes = [IsCustomerOrCaptain]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "sos"

    def get_throttles(self):
        return super().get_throttles() if self.request.method == "POST" else []

    def get(self, request):
        return Response(SosSerializer(SosAlert.objects.filter(user=request.user)[:20], many=True).data)

    def post(self, request):
        serializer = SosInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        alert = services.raise_sos(
            request.user, data.get("ride_id"), data.get("latitude"), data.get("longitude"), data["note"]
        )
        return Response(SosSerializer(alert).data, status=status.HTTP_201_CREATED)
