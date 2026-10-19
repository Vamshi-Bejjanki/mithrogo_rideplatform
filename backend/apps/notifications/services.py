from django.db import transaction

from apps.notifications.models import DeviceToken, Notification


def notify(user, notification_type, title, message="", data=None):
    """Store an in-app notification and push it to the user's devices once the transaction commits."""
    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        data=data or {},
    )

    def _push():
        from apps.notifications.push import push_to_user

        push_to_user(user, title, message, {"type": notification_type, "notification_id": notification.pk, **(data or {})})

    transaction.on_commit(_push)
    return notification


def notify_admins(notification_type, title, message="", data=None):
    """Alert every active admin (in-app and push). Used for SOS and other urgent events."""
    from apps.users.models import Role, User

    for admin in User.objects.filter(role=Role.ADMIN, is_active=True):
        notify(admin, notification_type, title, message, data)


def register_device(user, token, platform, app_version=""):
    """Save a push token. If another account used this phone before, the token moves to this user."""
    device, _ = DeviceToken.objects.update_or_create(
        token=token, defaults={"user": user, "platform": platform, "app_version": app_version}
    )
    return device


def unregister_device(user, token):
    DeviceToken.objects.filter(user=user, token=token).delete()
