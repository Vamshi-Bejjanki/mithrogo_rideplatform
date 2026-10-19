from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# app_label.model -> actions. "view" lets the role see it; "change" lets it run the admin actions.
ROLES = {
    "Operations": {
        "captains.captainprofile": ["view", "change"],
        "captains.kycdocument": ["view"],
        "vehicles.vehicle": ["view", "change"],
        "rides.ride": ["view"],
        "rides.rating": ["view"],
        "users.user": ["view"],
        "customers.customerprofile": ["view"],
        "support.supportticket": ["view", "change"],
        "support.sosalert": ["view", "change"],
        "notifications.notification": ["view", "add"],
        "subscriptions.captainsubscription": ["view"],
        "subscriptions.rideshareday": ["view"],
    },
    "Support": {
        "support.supportticket": ["view", "change"],
        "support.sosalert": ["view", "change"],
        "rides.ride": ["view"],
        "users.user": ["view"],
        "customers.customerprofile": ["view"],
        "captains.captainprofile": ["view"],
        "notifications.notification": ["view"],
    },
    "Finance": {
        "payments.payment": ["view"],
        "subscriptions.platformdue": ["view", "change"],
        "subscriptions.captainsubscription": ["view"],
        "subscriptions.subscriptionplan": ["view", "change"],
        "wallets.captainwallet": ["view"],
        "wallets.wallettransaction": ["view"],
        "rides.ride": ["view"],
        "rides.fareconfig": ["view", "change"],
        "promotions.promocode": ["view", "add", "change"],
        "promotions.promoredemption": ["view"],
    },
}


class Command(BaseCommand):
    """Create (or refresh) the Operations, Support and Finance admin groups. Safe to run again.

    Add a staff user to a group in admin (Users > user > Groups). Superusers keep full access.
    Reports need payments.view_payment; announcements need notifications.add_notification.
    """

    help = "Create or update the Operations, Support and Finance admin permission groups."

    def handle(self, *args, **options):
        for name, models in ROLES.items():
            group, created = Group.objects.get_or_create(name=name)
            permissions = []
            for label, actions in models.items():
                app_label, model = label.split(".")
                for action in actions:
                    perm = Permission.objects.filter(
                        content_type__app_label=app_label, codename=f"{action}_{model}"
                    ).first()
                    if perm is None:
                        self.stderr.write(f"Skipping missing permission {app_label}.{action}_{model}")
                        continue
                    permissions.append(perm)
            group.permissions.set(permissions)
            self.stdout.write(f"{'Created' if created else 'Updated'} group {name} ({len(permissions)} permissions)")
