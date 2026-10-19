from decimal import Decimal

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client

from core.models import AuditLog
from apps.captains.models import KycStatus
from apps.notifications.models import Notification
from apps.rides import services
from apps.rides.models import Ride, RideStatus
from apps.support.models import SosAlert, SupportTicket, TicketMessage
from apps.support.services import raise_sos
from apps.users.models import Role, User
from tests.helpers import make_captain, make_user, new_phone, ride_data

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(db):
    admin = User.objects.create_superuser(phone=new_phone(), password="admin-pass-123-long")
    client = Client()
    client.force_login(admin)
    return client, admin


def test_dashboard_has_charts_links_and_sos_banner(staff, customer):
    client, _ = staff
    raise_sos(customer, note="help")
    body = client.get("/admin/").content.decode()
    assert "Completed rides, last 14 days" in body
    assert "unresolved SOS alert needs attention" in body
    assert "/admin/live-map/" in body and "/admin/reports/" in body


def test_live_map_page_and_data(staff, customer, captain):
    client, _ = staff
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    assert client.get("/admin/live-map/").status_code == 200
    data = client.get("/admin/live-map/data/").json()
    assert data["rides"][0]["id"] == str(ride.id)
    assert data["captains"][0]["status"] == "BUSY"


def test_live_map_needs_staff(customer):
    client = Client()
    client.force_login(customer)
    assert client.get("/admin/live-map/data/").status_code == 302  # sent to the admin login


def test_reports_page_and_csv(staff, customer, captain):
    client, _ = staff
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(captain, ride.id)
    services.mark_arrived(captain, ride.id)
    services.start_ride(captain, ride.id, pin=ride.start_pin)
    services.complete_ride(captain, ride.id)

    page = client.get("/admin/reports/")
    assert page.status_code == 200 and "rides_completed" in page.content.decode()
    csv = client.get("/admin/reports/?export=csv")
    assert csv["Content-Type"] == "text/csv"
    earnings = client.get("/admin/reports/?report=earnings&export=csv").content.decode()
    assert captain.user.phone in earnings


def test_broadcast_page(staff, customer):
    client, _ = staff
    response = client.post("/admin/broadcast/", {"audience": "CUSTOMERS", "title": "Hi", "message": "Hello all"})
    assert response.status_code == 302
    assert Notification.objects.filter(user=customer, type="ANNOUNCEMENT").exists()
    assert AuditLog.objects.filter(action="admin.broadcast").exists()


def test_ride_page_shows_route_map_and_not_the_pin(staff, customer, captain):
    client, _ = staff
    ride = services.create_ride(customer, ride_data())
    body = client.get(f"/admin/rides/ride/{ride.id}/change/").content.decode()
    assert "ride-map" in body
    assert "field-start_pin " not in body and 'field-start_pin"' not in body  # the PIN row is excluded
    assert "field-start_pin_attempts" in body


def test_admin_cancel_ride_action_needs_reason(staff, customer, captain):
    client, _ = staff
    ride = services.create_ride(customer, ride_data())
    client.post("/admin/rides/ride/", {"action": "cancel_rides", "_selected_action": [str(ride.id)], "reason": ""})
    assert Ride.objects.get(pk=ride.id).status != RideStatus.CANCELLED
    client.post("/admin/rides/ride/", {"action": "cancel_rides", "_selected_action": [str(ride.id)],
                                       "reason": "Duplicate booking"})
    ride = Ride.objects.get(pk=ride.id)
    assert ride.status == RideStatus.CANCELLED and ride.cancelled_by == "ADMIN"
    assert ride.cancellation_note == "Duplicate booking"


def test_csv_export_action(staff, customer, captain):
    client, _ = staff
    ride = services.create_ride(customer, ride_data())
    response = client.post("/admin/rides/ride/", {"action": "export_csv", "_selected_action": [str(ride.id)]})
    assert response["Content-Type"] == "text/csv"
    assert str(ride.id) in response.content.decode()


def test_reject_kyc_requires_reason_and_tells_the_captain(staff):
    client, _ = staff
    captain = make_captain(approved=False, plan=None, online=False, location=None)
    url = "/admin/captains/captainprofile/"
    client.post(url, {"action": "reject_kyc", "_selected_action": [captain.pk], "reason": ""})
    captain.refresh_from_db()
    assert captain.kyc_status != KycStatus.REJECTED
    client.post(url, {"action": "reject_kyc", "_selected_action": [captain.pk], "reason": "RC expired"})
    captain.refresh_from_db()
    assert captain.kyc_status == KycStatus.REJECTED and captain.kyc_rejection_reason == "RC expired"
    assert Notification.objects.filter(user=captain.user, message__contains="RC expired").exists()
    page = client.get(f"/admin/captains/captainprofile/{captain.pk}/change/").content.decode()
    assert "Documents" in page


def test_ticket_reply_from_admin(staff, customer):
    client, _ = staff
    ticket = SupportTicket.objects.create(user=customer, category="OTHER", description="App crashed")
    response = client.post(f"/admin/support/supportticket/{ticket.pk}/change/", {
        "status": "OPEN", "resolution_note": "", "reply": "Please update the app.",
        "messages-TOTAL_FORMS": "0", "messages-INITIAL_FORMS": "0", "messages-MIN_NUM_FORMS": "0",
        "messages-MAX_NUM_FORMS": "1000",
    })
    assert response.status_code == 302, response.content.decode()[:2000]
    message = TicketMessage.objects.get(ticket=ticket)
    assert message.is_staff and message.body == "Please update the app."
    assert SupportTicket.objects.get(pk=ticket.pk).status == "IN_PROGRESS"
    assert Notification.objects.filter(user=customer, type="SUPPORT_REPLY").exists()


def test_sos_admin_actions(staff, customer):
    client, _ = staff
    alert = raise_sos(customer, note="help")
    assert client.get("/admin/support/sosalert/").status_code == 200
    client.post("/admin/support/sosalert/", {"action": "acknowledge", "_selected_action": [alert.pk]})
    assert SosAlert.objects.get(pk=alert.pk).status == "ACKNOWLEDGED"
    client.post("/admin/support/sosalert/", {"action": "resolve", "_selected_action": [alert.pk], "reason": "Safe"})
    assert SosAlert.objects.get(pk=alert.pk).status == "RESOLVED"


def test_new_model_pages_load(staff):
    client, _ = staff
    for url in ["/admin/promotions/promocode/", "/admin/promotions/promoredemption/",
                "/admin/customers/savedplace/", "/admin/notifications/devicetoken/", "/admin/promotions/promocode/add/"]:
        assert client.get(url).status_code == 200, url


def test_setup_admin_roles_and_permission_gates():
    call_command("setup_admin_roles")
    support = Group.objects.get(name="Support")
    assert support.permissions.filter(codename="change_supportticket").exists()
    assert not support.permissions.filter(codename="view_payment").exists()

    agent = User.objects.create_user(phone=new_phone(), password="agent-pass-123", role=Role.ADMIN, is_staff=True)
    agent.groups.add(support)
    client = Client()
    client.force_login(agent)
    assert client.get("/admin/support/supportticket/").status_code == 200
    assert client.get("/admin/reports/").status_code == 403
    assert client.get("/admin/broadcast/").status_code == 403
    call_command("setup_admin_roles")  # running again is safe
    assert Group.objects.filter(name__in=["Operations", "Support", "Finance"]).count() == 3
