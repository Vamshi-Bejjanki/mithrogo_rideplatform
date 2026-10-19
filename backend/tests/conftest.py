from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import Role
from tests.helpers import make_captain, make_user


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def _capture_sms(settings):
    from tests.helpers import CapturingSmsProvider

    CapturingSmsProvider.sent = []
    CapturingSmsProvider.fail = False
    settings.SMS_PROVIDER = "tests.helpers.CapturingSmsProvider"
    yield


@pytest.fixture
def clock(monkeypatch):
    """Controllable 'now' for offer timeouts and ride-share day boundaries."""

    class Clock:
        def __init__(self):
            self.now = timezone.now()

        def __call__(self):
            return self.now

        def advance(self, **kwargs):
            self.now += timedelta(**kwargs)

    fake = Clock()
    monkeypatch.setattr(timezone, "now", fake)
    return fake


@pytest.fixture
def customer(db):
    return make_user(Role.CUSTOMER, first_name="Asha")


@pytest.fixture
def captain(db):
    return make_captain()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def as_user(api):
    """Authenticate the API client as a given user (bypasses OTP; OTP has its own tests)."""

    def _login(user):
        api.force_authenticate(user=user)
        return api

    return _login
