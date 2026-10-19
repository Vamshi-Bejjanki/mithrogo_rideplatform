from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db.models import Q, Sum
from django.utils import timezone


def service_day_start(now):
    """Midnight at the start of the business day, in the configured service timezone."""
    from core.models import PlatformConfig

    tz = ZoneInfo(PlatformConfig.load().service_timezone)
    local = now.astimezone(tz)
    return datetime(local.year, local.month, local.day, tzinfo=tz)


def dashboard_metrics():
    """Counts and totals for the admin dashboard. Read-only."""
    from apps.captains.models import CaptainProfile, KycStatus, OnlineStatus
    from apps.payments.models import Payment, PaymentStatus, PaymentType
    from apps.rides.models import ACTIVE_STATUSES, Ride, RideStatus
    from apps.subscriptions.models import DueStatus, PlatformDue
    from apps.support.models import SosAlert, SosStatus, SupportTicket, TicketStatus
    from apps.users.models import Role, User

    now = timezone.now()
    day_start = service_day_start(now)

    def revenue(payment_type):
        total = Payment.objects.filter(payment_type=payment_type, status=PaymentStatus.SUCCESS).aggregate(
            total=Sum("amount")
        )["total"]
        return total or Decimal("0")

    dues = PlatformDue.objects.filter(status=DueStatus.PENDING).aggregate(total=Sum("amount"))["total"]

    return {
        "total_customers": User.objects.filter(role=Role.CUSTOMER).count(),
        "total_captains": CaptainProfile.objects.count(),
        "online_captains": CaptainProfile.objects.filter(online_status=OnlineStatus.ONLINE).count(),
        "pending_kyc": CaptainProfile.objects.filter(
            kyc_status__in=[KycStatus.PENDING, KycStatus.UNDER_REVIEW]
        ).count(),
        "active_rides": Ride.objects.filter(status__in=ACTIVE_STATUSES).count(),
        "completed_today": Ride.objects.filter(status=RideStatus.COMPLETED, completed_at__gte=day_start).count(),
        "cancelled_today": Ride.objects.filter(status=RideStatus.CANCELLED, cancelled_at__gte=day_start).count(),
        "subscription_revenue": revenue(PaymentType.CAPTAIN_SUBSCRIPTION),
        "ride_revenue": revenue(PaymentType.RIDE_PAYMENT),
        "pending_platform_dues": dues or Decimal("0"),
        "open_tickets": SupportTicket.objects.filter(
            Q(status=TicketStatus.OPEN) | Q(status=TicketStatus.IN_PROGRESS)
        ).count(),
        "open_sos": SosAlert.objects.exclude(status=SosStatus.RESOLVED).count(),
        "fee_revenue": revenue(PaymentType.CANCELLATION_FEE),
        "busy_captains": CaptainProfile.objects.filter(online_status=OnlineStatus.BUSY).count(),
    }
