from django.urls import path

from apps.notifications.views import DeviceView, NotificationListView, NotificationReadView, ReadAllView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications"),
    path("<int:pk>/read/", NotificationReadView.as_view(), name="notification-read"),
    path("read-all/", ReadAllView.as_view(), name="notification-read-all"),
    path("devices/", DeviceView.as_view(), name="notification-devices"),
]
