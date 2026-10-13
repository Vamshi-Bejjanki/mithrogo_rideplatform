from apps.notifications.models import Notification


def notify(user, notification_type, title, message="", data=None):
    """Store an in-app notification. Push delivery (FCM) hooks in here later, via Celery."""
    return Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        data=data or {},
    )
