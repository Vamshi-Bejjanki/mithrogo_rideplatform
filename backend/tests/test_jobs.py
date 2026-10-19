import pytest
from django.core.management import call_command

from apps.notifications.models import Notification
from apps.subscriptions.models import CaptainSubscription, SubStatus
from tests.helpers import make_captain


@pytest.mark.django_db
def test_periodic_job_expires_a_daily_plan_and_notifies_the_captain(clock):
    captain = make_captain(location=None, online=False)
    sub = CaptainSubscription.objects.get(captain=captain, status=SubStatus.ACTIVE)

    clock.advance(hours=12, minutes=1)
    call_command("run_periodic_jobs")

    sub.refresh_from_db()
    assert sub.status == SubStatus.EXPIRED
    assert Notification.objects.filter(user=captain.user, type="SUBSCRIPTION_EXPIRED").exists()


@pytest.mark.django_db
def test_periodic_job_is_safe_to_run_repeatedly(clock):
    make_captain(location=None, online=False)
    clock.advance(hours=12, minutes=1)

    call_command("run_periodic_jobs")
    call_command("run_periodic_jobs")

    assert Notification.objects.filter(type="SUBSCRIPTION_EXPIRED").count() == 1
