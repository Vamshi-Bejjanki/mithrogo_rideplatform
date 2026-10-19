from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from core.models import AuditLog
from apps.notifications.models import DeviceToken, Notification
from apps.rides import services
from apps.subscriptions.models import CaptainSubscription, SubStatus
from apps.subscriptions.services import active_subscription, remind_expiring_subscriptions
from apps.support.models import SosAlert, SupportTicket
from apps.users.models import Role, User
from tests.helpers import make_captain, make_user, ride_data

pytestmark = pytest.mark.django_db


def client_for(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(phone="+919000000001", password="s3cret-pass", first_name="Ops")


@pytest.fixture
def admin_api(admin_user):
    return client_for(admin_user)


# ---------- tickets ----------

def test_ticket_conversation(customer, admin_api):
    api = client_for(customer)
    ticket = api.post("/api/v1/support/tickets/", {"category": "PAYMENT", "description": "Charged twice"},
                      format="json").json()

    reply = admin_api.post(f"/api/v1/admin/tickets/{ticket['id']}/reply/", {"body": "Refund started."}, format="json")
    assert reply.status_code == 201
    assert Notification.objects.filter(user=customer, type="SUPPORT_REPLY").exists()

    detail = api.get(f"/api/v1/support/tickets/{ticket['id']}/").json()
    assert detail["status"] == "IN_PROGRESS"
    assert detail["messages"][0] == {**detail["messages"][0], "is_staff": True, "author_name": "MithroGo Support"}

    admin_api.post(f"/api/v1/admin/tickets/{ticket['id']}/status/", {"status": "RESOLVED", "note": "Refunded"},
                   format="json")
    api.post(f"/api/v1/support/tickets/{ticket['id']}/messages/", {"body": "Not received yet"}, format="json")
    assert SupportTicket.objects.get(pk=ticket["id"]).status == "OPEN"  # a reply reopens it
    assert len(api.get(f"/api/v1/support/tickets/{ticket['id']}/messages/").json()) == 2


def test_users_cannot_read_other_tickets(customer):
    other = make_user(Role.CUSTOMER)
    ticket = SupportTicket.objects.create(user=other, category="OTHER", description="x")
    assert client_for(customer).get(f"/api/v1/support/tickets/{ticket.pk}/").status_code == 404


# ---------- SOS ----------

def test_sos_alerts_every_admin_and_attaches_the_active_ride(customer, captain, admin_user, admin_api):
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    response = client_for(customer).post(
        "/api/v1/support/sos/", {"latitude": "18.672500", "longitude": "78.094000", "note": "Help"}, format="json"
    )
    assert response.status_code == 201
    alert = SosAlert.objects.get(pk=response.json()["id"])
    assert alert.ride_id == ride.id and alert.ticket.category == "SAFETY"
    assert Notification.objects.filter(user=admin_user, type="SOS_ALERT").exists()

    listed = admin_api.get("/api/v1/admin/sos/?status=OPEN").json()
    assert listed["count"] == 1
    assert admin_api.post(f"/api/v1/admin/sos/{alert.pk}/acknowledge/").json()["status"] == "ACKNOWLEDGED"
    assert Notification.objects.filter(user=customer, type="SOS_ACKNOWLEDGED").exists()
    resolved = admin_api.post(f"/api/v1/admin/sos/{alert.pk}/resolve/", {"reason": "Rider safe"}, format="json")
    assert resolved.json()["status"] == "RESOLVED"
    assert SupportTicket.objects.get(pk=alert.ticket_id).status == "RESOLVED"
    assert AuditLog.objects.filter(action="api.resolve_sos").exists()


def test_captain_can_raise_sos_too(captain):
    assert client_for(captain.user).post("/api/v1/support/sos/", {}, format="json").status_code == 201


# ---------- devices and push ----------

def test_device_registration_and_push(customer, captain, settings):
    pushed = []
    settings.PUSH_PROVIDER = "tests.test_support_and_backoffice.RecorderProvider"
    RecorderProvider.calls = pushed
    api = client_for(customer)
    assert api.post("/api/v1/notifications/devices/", {"token": "tok-1", "platform": "ANDROID"},
                    format="json").status_code == 201
    DeviceToken.objects.create(user=customer, token="dead-token", platform="ANDROID")

    # notify() pushes on commit, which never fires inside a test transaction, so push directly.
    from apps.notifications.push import push_to_user

    push_to_user(customer, "Hello", "World", {"ride_id": "r1"})
    assert pushed and set(pushed[-1][0]) == {"tok-1", "dead-token"}
    assert not DeviceToken.objects.filter(token="dead-token").exists()  # invalid tokens are pruned

    assert api.delete("/api/v1/notifications/devices/", {"token": "tok-1"}, format="json").status_code == 204
    assert not DeviceToken.objects.filter(user=customer).exists()


class RecorderProvider:
    calls = []

    def send(self, tokens, title, body, data):
        RecorderProvider.calls.append((tokens, title, data))
        return ["dead-token"]


def test_mark_all_notifications_read(customer):
    from apps.notifications.services import notify

    notify(customer, "A", "a")
    notify(customer, "B", "b")
    assert client_for(customer).post("/api/v1/notifications/read-all/").json() == {"marked_read": 2}


# ---------- plan reminders ----------

def test_plan_expiry_reminder_is_sent_once(clock):
    captain = make_captain()
    sub = CaptainSubscription.objects.get(captain=captain, status=SubStatus.ACTIVE)
    clock.now = sub.expires_at - timedelta(minutes=30)
    assert remind_expiring_subscriptions() == 1
    assert remind_expiring_subscriptions() == 0
    assert Notification.objects.filter(user=captain.user, type="SUBSCRIPTION_EXPIRING").count() == 1


def test_lazy_expiry_notifies_once(clock):
    captain = make_captain(online=False)
    sub = CaptainSubscription.objects.get(captain=captain, status=SubStatus.ACTIVE)
    clock.now = sub.expires_at + timedelta(minutes=1)
    assert active_subscription(captain) is None
    assert active_subscription(captain) is None
    assert Notification.objects.filter(user=captain.user, type="SUBSCRIPTION_EXPIRED").count() == 1


# ---------- admin API ----------

def test_admin_api_is_admin_only(customer, captain):
    assert client_for(customer).get("/api/v1/admin/dashboard/").status_code == 403
    assert client_for(captain.user).get("/api/v1/admin/rides/").status_code == 403
    assert APIClient().get("/api/v1/admin/dashboard/").status_code == 401


def test_admin_login(admin_user, customer, api):
    ok = api.post("/api/v1/auth/admin/login/", {"phone": "+919000000001", "password": "s3cret-pass"}, format="json")
    assert ok.status_code == 200 and ok.json()["user"]["role"] == "ADMIN" and ok.json()["access"]
    bad = api.post("/api/v1/auth/admin/login/", {"phone": "+919000000001", "password": "nope"}, format="json")
    assert bad.status_code == 400 and bad.json()["code"] == "invalid_credentials"
    customer.set_password("pw-123456")
    customer.save()
    not_admin = api.post("/api/v1/auth/admin/login/", {"phone": customer.phone, "password": "pw-123456"},
                         format="json")
    assert not_admin.status_code == 400


def test_dashboard_and_reports(admin_api, customer, captain):
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    dashboard = admin_api.get("/api/v1/admin/dashboard/").json()
    assert dashboard["metrics"]["active_rides"] == 1
    assert len(dashboard["last_7_days"]) == 7

    report = admin_api.get("/api/v1/admin/reports/daily/").json()
    assert report["totals"]["rides_requested"] == 1
    csv_response = admin_api.get("/api/v1/admin/reports/daily/?export=csv")
    assert csv_response["Content-Type"].startswith("text/csv")
    assert csv_response.content.decode().splitlines()[0].startswith("date,rides_requested")


def test_ride_list_detail_timeline_and_live(admin_api, customer, captain):
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    listed = admin_api.get(f"/api/v1/admin/rides/?status=ACCEPTED&search={customer.phone}").json()
    assert listed["count"] == 1

    detail = admin_api.get(f"/api/v1/admin/rides/{ride.id}/").json()
    assert [e["to_status"] for e in detail["events"]] == ["REQUESTED", "SEARCHING", "ACCEPTED"]
    assert detail["offers"][0]["status"] == "ACCEPTED"

    live = admin_api.get("/api/v1/admin/rides/live/").json()
    assert live["rides"][0]["captain_location"] is not None

    cancel = admin_api.post(f"/api/v1/admin/rides/{ride.id}/cancel/", {"reason": "Rider called support"},
                            format="json")
    assert cancel.json()["status"] == "CANCELLED" and cancel.json()["cancelled_by"] == "ADMIN"


def test_captain_kyc_actions_and_reject_needs_reason(admin_api):
    captain = make_captain(approved=False, plan=None, online=False, location=None)
    no_reason = admin_api.post(f"/api/v1/admin/captains/{captain.pk}/reject/", {}, format="json")
    assert no_reason.status_code == 400 and no_reason.json()["code"] == "reason_required"

    rejected = admin_api.post(f"/api/v1/admin/captains/{captain.pk}/reject/", {"reason": "Licence photo blurry"},
                              format="json").json()
    assert rejected["kyc_status"] == "REJECTED" and rejected["kyc_rejection_reason"] == "Licence photo blurry"
    assert Notification.objects.filter(user=captain.user, message__contains="Licence photo blurry").exists()

    assert admin_api.post(f"/api/v1/admin/captains/{captain.pk}/approve/").json()["kyc_status"] == "APPROVED"
    assert AuditLog.objects.filter(action__in=["api.reject_kyc", "api.approve_captain"]).count() == 2

    vehicle = captain.vehicles.first()
    assert admin_api.post(f"/api/v1/admin/vehicles/{vehicle.pk}/verify/").json()["is_verified"] is True


def test_customer_suspend_and_list(admin_api, customer):
    assert admin_api.get("/api/v1/admin/customers/?search=Asha").json()["count"] == 1
    assert admin_api.post(f"/api/v1/admin/customers/{customer.pk}/suspend/").json()["is_active"] is False
    customer.refresh_from_db()
    assert customer.is_active is False


def test_config_fares_and_promos_are_audited(admin_api):
    patched = admin_api.patch("/api/v1/admin/config/", {"customer_cancel_fee": "15.00"}, format="json")
    assert patched.status_code == 200 and patched.json()["customer_cancel_fee"] == "15.00"
    entry = AuditLog.objects.get(action="api.update_platform_config")
    assert entry.changes["customer_cancel_fee"] == ["0.00", "15.00"]

    fare = admin_api.get("/api/v1/admin/fares/").json()[0]
    assert admin_api.patch(f"/api/v1/admin/fares/{fare['id']}/", {"per_km": "9.50"}, format="json").status_code == 200

    promo = admin_api.post("/api/v1/admin/promos/", {"code": "launch", "discount_type": "PERCENT", "value": "20",
                                                     "max_discount": "40"}, format="json")
    assert promo.status_code == 201 and promo.json()["code"] == "LAUNCH"
    too_much = admin_api.post("/api/v1/admin/promos/", {"code": "X", "discount_type": "PERCENT", "value": "150"},
                              format="json")
    assert too_much.status_code == 400


def test_broadcast(admin_api, customer, captain):
    response = admin_api.post("/api/v1/admin/broadcast/", {"audience": "CUSTOMERS", "title": "Diwali offer",
                                                           "message": "20% off"}, format="json")
    assert response.json()["recipients"] == 1
    assert Notification.objects.filter(user=customer, type="ANNOUNCEMENT").exists()
    assert not Notification.objects.filter(user=captain.user, type="ANNOUNCEMENT").exists()


def test_dues_and_audit_log(admin_api, captain):
    from decimal import Decimal

    from apps.subscriptions.models import PlatformDue

    due = PlatformDue.objects.create(captain=captain, due_type="SHORTFALL_FEE", amount=Decimal("30"))
    assert admin_api.post(f"/api/v1/admin/dues/{due.pk}/waive/").json()["status"] == "WAIVED"
    assert admin_api.post(f"/api/v1/admin/dues/{due.pk}/waive/").status_code == 409
    log = admin_api.get("/api/v1/admin/audit-log/?action=api.waive_due").json()
    assert log["count"] == 1


def test_notify_pushes_after_commit(customer, settings, django_capture_on_commit_callbacks):
    from apps.notifications.services import notify

    settings.PUSH_PROVIDER = "tests.test_support_and_backoffice.RecorderProvider"
    RecorderProvider.calls = []
    DeviceToken.objects.create(user=customer, token="tok-9", platform="IOS")
    with django_capture_on_commit_callbacks(execute=True):
        notify(customer, "RIDE_ACCEPTED", "Captain accepted", "On the way", {"ride_id": "r9"})
    tokens, title, data = RecorderProvider.calls[-1]
    assert tokens == ["tok-9"] and title == "Captain accepted"
    assert data["type"] == "RIDE_ACCEPTED" and data["ride_id"] == "r9"
