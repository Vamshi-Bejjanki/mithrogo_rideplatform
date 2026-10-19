from core.exceptions import Forbidden
from apps.users.models import Role, User


def provision_profile(user):
    """Create the role-specific profile row the first time a user logs in."""
    if user.role == Role.CUSTOMER:
        from apps.customers.services import ensure_profile

        ensure_profile(user)
    elif user.role == Role.CAPTAIN:
        from apps.captains.services import ensure_profile

        ensure_profile(user)


def login_for_role(phone, role):
    """Return the user for this phone and app role, creating the account on first login.

    A phone number belongs to one role only, so a captain number cannot sign in to the customer app.
    """
    user = User.objects.filter(phone=phone).first()
    if user is None:
        user = User.objects.create_user(phone=phone, role=role, is_verified=True)
        provision_profile(user)
    elif user.role != role:
        raise Forbidden(
            f"This number is registered as a {user.role.lower()}. Use the {user.role.lower()} app.",
            code="wrong_role",
        )
    if not user.is_active:
        raise Forbidden("This account is suspended. Contact support.", code="account_suspended")
    if not user.is_verified:
        user.is_verified = True
        user.save(update_fields=["is_verified"])
    return user
