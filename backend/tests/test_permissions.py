import pytest

from apps.notifications.models import Notification
from apps.payments.models import PaymentType
from apps.payments import services as payment_services
from apps.rides import services
from apps.users.models import Role
from tests.helpers import NEAR_PICKUP, make_captain, make_user, ride_data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "method, url",
    [
        ("get", "/api/v1/captains/profile/"),
        ("post", "/api/v1/captains/status/online/"),
        ("get", "/api/v1/captains/offers/"),
        ("get", "/api/v1/captains/subscription/"),
        ("get", "/api/v1/captains/subscription/plans/"),
        ("get", "/api/v1/captains/earnings/"),
    ],
)
def test_customer_cannot_use_captain_endpoints(as_user, customer, method, url):
    response = getattr(as_user(customer), method)(url)

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "method, url",
    [
        ("get", "/api/v1/rides/"),
        ("post", "/api/v1/rides/estimate/"),
        ("get", "/api/v1/customers/profile/"),
    ],
)
def test_captain_cannot_use_customer_endpoints(as_user, method, url):
    captain = make_captain()
    api = as_user(captain.user)

    response = api.post(url, {}, format="json") if method == "post" else api.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("url", ["/api/v1/rides/", "/api/v1/captains/profile/", "/api/v1/notifications/"])
def test_anonymous_requests_are_rejected(api, url):
    assert api.get(url).status_code == 401


@pytest.mark.django_db
def test_captain_cannot_open_another_captains_ride(as_user, customer):
    owner = make_captain(location=NEAR_PICKUP)
    other = make_captain(location=NEAR_PICKUP)
    ride = services.create_ride(customer, ride_data())
    services.accept_offer(owner, ride.id)

    response = as_user(other.user).get(f"/api/v1/captains/rides/{ride.id}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_customer_cannot_read_another_customers_payment_or_notifications(as_user):
    owner = make_user(Role.CUSTOMER)
    intruder = make_user(Role.CUSTOMER)
    payment = payment_services.create_payment(owner, PaymentType.RIDE_PAYMENT, 40, {"ride_id": "x"})
    note = Notification.objects.create(user=owner, type="T", title="Private")

    assert as_user(intruder).get(f"/api/v1/payments/{payment.id}/").status_code == 404
    assert as_user(intruder).post(f"/api/v1/notifications/{note.pk}/read/").status_code == 404


@pytest.mark.django_db
def test_support_ticket_must_reference_the_users_own_ride(as_user, customer):
    make_captain(location=NEAR_PICKUP)
    stranger = make_user(Role.CUSTOMER)
    someone_elses_ride = services.create_ride(stranger, ride_data())

    response = as_user(customer).post(
        "/api/v1/support/tickets/",
        {"category": "RIDE_ISSUE", "description": "Wrong fare", "ride_id": str(someone_elses_ride.id)},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ride_not_yours"
