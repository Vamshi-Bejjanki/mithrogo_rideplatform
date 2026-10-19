"""Push delivery. Pluggable like SMS: settings.PUSH_PROVIDER names the class.

The default logs pushes (development). A Firebase (FCM HTTP v1) provider implements the same
`send` method once the Firebase service-account credentials are available.
"""

import logging

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class PushProvider:
    def send(self, tokens, title, body, data):
        """Deliver to these device tokens. Returns the tokens the gateway reported as invalid."""
        raise NotImplementedError


class LogPushProvider(PushProvider):
    def send(self, tokens, title, body, data):
        logger.info("Push to %d device(s): %s - %s %s", len(tokens), title, body, data)
        return []


def get_provider():
    return import_string(getattr(settings, "PUSH_PROVIDER", "apps.notifications.push.LogPushProvider"))()


def push_to_user(user, title, body, data=None):
    """Best effort: a failed push never breaks the business action that triggered it."""
    from apps.notifications.models import DeviceToken

    tokens = list(DeviceToken.objects.filter(user=user).values_list("token", flat=True))
    if not tokens:
        return
    try:
        invalid = get_provider().send(tokens, title, body, {k: str(v) for k, v in (data or {}).items()})
    except Exception:  # noqa: BLE001 - push is best effort by design
        logger.exception("Push delivery failed for user %s", user.pk)
        return
    if invalid:
        DeviceToken.objects.filter(token__in=invalid).delete()
