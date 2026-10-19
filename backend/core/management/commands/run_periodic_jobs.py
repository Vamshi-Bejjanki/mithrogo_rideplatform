from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Run every minute from cron or Task Scheduler (replace with Celery beat later).

    - reminds captains whose daily plan is about to end
    - expires daily subscriptions past their end time
    - closes finished ride-share days (applies shortfall fees)
    - expires ride offers that timed out and offers the ride to the next captain
    """

    help = "Expire subscriptions, close finished ride-share days, and advance timed-out ride offers."

    def handle(self, *args, **options):
        from apps.rides.services import sweep_searching_rides
        from apps.subscriptions.services import (
            close_all_stale_days,
            expire_subscriptions,
            remind_expiring_subscriptions,
        )

        reminded = remind_expiring_subscriptions()
        expired = expire_subscriptions()
        closed = close_all_stale_days()
        advanced = sweep_searching_rides()
        self.stdout.write(
            f"reminded_subscriptions={reminded} expired_subscriptions={expired} "
            f"closed_ride_share_days={closed} advanced_rides={advanced}"
        )
