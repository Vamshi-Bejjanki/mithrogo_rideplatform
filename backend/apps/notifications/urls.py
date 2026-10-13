from django.urls import path

from apps.notifications.views import NotificationListView, NotificationReadView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications"),
    path("<int:pk>/read/", NotificationReadView.as_view(), name="notification-read"),
]
