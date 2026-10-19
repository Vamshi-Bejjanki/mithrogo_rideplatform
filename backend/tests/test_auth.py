import pytest

from apps.customers.models import CustomerProfile
from apps.users.models import User
from apps.users.models import OtpChallenge
from tests.helpers import last_code_sent_to, make_user, new_phone

from apps.users.models import Role

SEND = "/api/v1/auth/send-otp/"
VERIFY = "/api/v1/auth/verify-otp/"


def send_code(api, phone):
    response = api.post(SEND, {"phone": phone}, format="json")
    assert response.status_code == 200, response.content
    assert "dev_code" not in response.json()
    return last_code_sent_to(phone)


@pytest.mark.django_db
def test_otp_login_creates_customer_and_issues_tokens(api):
    phone = new_phone()
    code = send_code(api, phone)

    response = api.post(VERIFY, {"phone": phone, "code": code, "role": "CUSTOMER"}, format="json")

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == "CUSTOMER"
    assert body["access"] and body["refresh"]
    assert CustomerProfile.objects.filter(user__phone=phone).exists()


@pytest.mark.django_db
def test_wrong_code_is_rejected(api):
    phone = new_phone()
    send_code(api, phone)

    response = api.post(VERIFY, {"phone": phone, "code": "000000", "role": "CUSTOMER"}, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "otp_invalid"


@pytest.mark.django_db
def test_code_is_locked_after_too_many_wrong_attempts(api):
    phone = new_phone()
    code = send_code(api, phone)
    for _ in range(5):
        api.post(VERIFY, {"phone": phone, "code": "000000", "role": "CUSTOMER"}, format="json")

    response = api.post(VERIFY, {"phone": phone, "code": code, "role": "CUSTOMER"}, format="json")

    assert response.status_code == 429
    assert response.json()["code"] == "otp_locked"


@pytest.mark.django_db
def test_code_cannot_be_reused(api):
    phone = new_phone()
    code = send_code(api, phone)
    assert api.post(VERIFY, {"phone": phone, "code": code, "role": "CUSTOMER"}, format="json").status_code == 200

    response = api.post(VERIFY, {"phone": phone, "code": code, "role": "CUSTOMER"}, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "otp_not_found"


@pytest.mark.django_db
def test_sending_more_than_five_codes_per_hour_is_refused(api):
    phone = new_phone()
    for _ in range(5):
        send_code(api, phone)

    response = api.post(SEND, {"phone": phone}, format="json")

    assert response.status_code == 429
    assert response.json()["code"] == "otp_rate_limited"


@pytest.mark.django_db
@pytest.mark.parametrize("bad", ["12345", "9812345678", "+91 abc", ""])
def test_invalid_phone_numbers_are_rejected(api, bad):
    response = api.post(SEND, {"phone": bad}, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_captain_number_cannot_sign_in_to_customer_app(api):
    captain_user = make_user(Role.CAPTAIN)
    code = send_code(api, captain_user.phone)

    response = api.post(VERIFY, {"phone": captain_user.phone, "code": code, "role": "CUSTOMER"}, format="json")

    assert response.status_code == 403
    assert response.json()["code"] == "wrong_role"


@pytest.mark.django_db
def test_suspended_user_cannot_sign_in(api):
    user = make_user(Role.CUSTOMER)
    user.is_active = False
    user.save(update_fields=["is_active"])
    code = send_code(api, user.phone)

    response = api.post(VERIFY, {"phone": user.phone, "code": code, "role": "CUSTOMER"}, format="json")

    assert response.status_code == 403
    assert response.json()["code"] == "account_suspended"


@pytest.mark.django_db
def test_me_requires_authentication(api):
    assert api.get("/api/v1/auth/me/").status_code == 401


@pytest.mark.django_db
def test_me_returns_the_signed_in_user(api, customer, as_user):
    response = as_user(customer).get("/api/v1/auth/me/")

    assert response.status_code == 200
    assert response.json()["phone"] == customer.phone


@pytest.mark.django_db
def test_logout_blacklists_the_refresh_token(api):
    phone = new_phone()
    code = send_code(api, phone)
    tokens = api.post(VERIFY, {"phone": phone, "code": code, "role": "CUSTOMER"}, format="json").json()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    logout = api.post("/api/v1/auth/logout/", {"refresh": tokens["refresh"]}, format="json")
    refreshed = api.post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")

    assert logout.status_code == 204
    assert refreshed.status_code == 401


@pytest.mark.django_db
def test_admin_role_cannot_use_otp_login(api):
    admin = User.objects.create_superuser(phone=new_phone(), password="x-long-password-123")
    code = send_code(api, admin.phone)

    response = api.post(VERIFY, {"phone": admin.phone, "code": code, "role": "CAPTAIN"}, format="json")

    assert response.status_code == 403



@pytest.mark.django_db
def test_code_is_only_delivered_by_sms(api):
    phone = new_phone()

    response = api.post(SEND, {"phone": phone}, format="json")

    assert response.status_code == 200
    assert response.json() == {"detail": "Code sent."}
    assert last_code_sent_to(phone)


@pytest.mark.django_db
def test_failed_sms_is_reported_and_leaves_no_usable_code(api):
    from tests.helpers import CapturingSmsProvider

    phone = new_phone()
    CapturingSmsProvider.fail = True

    response = api.post(SEND, {"phone": phone}, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "sms_failed"
    assert not OtpChallenge.objects.filter(phone=phone).exists()
