from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import DevicePlatform, Notification
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import register_device, unregister_device


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)[:100]


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)


class DeviceSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=DevicePlatform.choices, required=False, default=DevicePlatform.ANDROID)
    app_version = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")


class DeviceView(APIView):
    """POST registers this phone's push token; DELETE (body: token) removes it, e.g. on logout."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        device = register_device(request.user, data["token"], data["platform"], data["app_version"])
        return Response({"token": device.token, "platform": device.platform}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        token = (request.data or {}).get("token") or request.query_params.get("token", "")
        unregister_device(request.user, token)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"marked_read": updated})
