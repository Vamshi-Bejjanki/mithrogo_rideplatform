from apps.customers.models import CustomerProfile


def ensure_profile(user):
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile
