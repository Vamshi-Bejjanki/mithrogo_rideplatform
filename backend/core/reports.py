"""Read-only reports shared by Django Admin and the admin REST API: daily series and CSV exports."""

import csv
import io
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate

MAX_DAYS = 366


def _tz():
    from core.models import PlatformConfig

    return ZoneInfo(PlatformConfig.load().service_timezone)


def parse_range(start=None, end=None, default_days=14):
    """Inclusive date range in the service timezone. Bad or missing values fall back to the last N days."""
    tz = _tz()
    today = datetime.now(tz).date()

    def _parse(value):
        try:
            return date.fromisoformat(value) if value else None
        except ValueError:
            return None

    end_date = _parse(end) or today
    start_date = _parse(start) or end_date - timedelta(days=default_days - 1)
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    if (end_date - start_date).days >= MAX_DAYS:
        start_date = end_date - timedelta(days=MAX_DAYS - 1)
    return start_date, end_date


def _bounds(start_date, end_date):
    tz = _tz()
    return datetime.combine(start_date, time.min, tz), datetime.combine(end_date + timedelta(days=1), time.min, tz)


def _days(start_date, end_date):
    return [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]


def daily_report(start_date, end_date):
    """One row per day: rides requested, completed, cancelled, gross fares, and money received by type."""
    from apps.payments.models import Payment, PaymentStatus, PaymentType
    from apps.rides.models import Ride, RideStatus

    tz = _tz()
    since, until = _bounds(start_date, end_date)

    rides = (
        Ride.objects.filter(requested_at__gte=since, requested_at__lt=until)
        .annotate(day=TruncDate("requested_at", tzinfo=tz))
        .values("day")
        .annotate(
            requested=Count("id"),
            completed=Count("id", filter=Q(status=RideStatus.COMPLETED)),
            cancelled=Count("id", filter=Q(status=RideStatus.CANCELLED)),
            bike=Count("id", filter=Q(vehicle_type="BIKE")),
            auto=Count("id", filter=Q(vehicle_type="AUTO")),
            fares=Sum("final_fare", filter=Q(status=RideStatus.COMPLETED)),
            discounts=Sum("discount_amount", filter=Q(status=RideStatus.COMPLETED)),
            platform_share=Sum("platform_share_amount", filter=Q(status=RideStatus.COMPLETED)),
        )
    )
    payments = (
        Payment.objects.filter(status=PaymentStatus.SUCCESS, updated_at__gte=since, updated_at__lt=until)
        .annotate(day=TruncDate("updated_at", tzinfo=tz))
        .values("day", "payment_type")
        .annotate(total=Sum("amount"))
    )

    zero = Decimal("0")
    by_day = {
        d: {
            "date": d.isoformat(), "rides_requested": 0, "rides_completed": 0, "rides_cancelled": 0,
            "bike_rides": 0, "auto_rides": 0, "gross_fares": zero, "discounts": zero, "platform_share": zero,
            "subscription_revenue": zero, "ride_payments": zero, "dues_collected": zero,
            "wallet_top_ups": zero, "fee_revenue": zero,
        }
        for d in _days(start_date, end_date)
    }
    for row in rides:
        if row["day"] not in by_day:
            continue
        entry = by_day[row["day"]]
        entry.update(
            rides_requested=row["requested"], rides_completed=row["completed"], rides_cancelled=row["cancelled"],
            bike_rides=row["bike"], auto_rides=row["auto"], gross_fares=row["fares"] or zero,
            discounts=row["discounts"] or zero, platform_share=row["platform_share"] or zero,
        )
    column = {
        PaymentType.CAPTAIN_SUBSCRIPTION: "subscription_revenue",
        PaymentType.RIDE_PAYMENT: "ride_payments",
        PaymentType.DUES_SETTLEMENT: "dues_collected",
        PaymentType.WALLET_TOP_UP: "wallet_top_ups",
        PaymentType.CANCELLATION_FEE: "fee_revenue",
    }
    for row in payments:
        if row["day"] in by_day and row["payment_type"] in column:
            by_day[row["day"]][column[row["payment_type"]]] += row["total"] or zero

    result = list(by_day.values())
    for entry in result:
        for key, value in entry.items():
            if isinstance(value, Decimal):
                entry[key] = str(value.quantize(Decimal("0.01")))
    return result


def report_totals(rows):
    totals = {}
    for row in rows:
        for key, value in row.items():
            if key == "date":
                continue
            current = totals.get(key, Decimal("0") if isinstance(value, str) else 0)
            totals[key] = current + (Decimal(value) if isinstance(value, str) else value)
    return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in totals.items()}


def captain_earnings_report(start_date, end_date):
    """Per-captain completed rides, fares and platform share for the period."""
    from apps.rides.models import Ride, RideStatus

    since, until = _bounds(start_date, end_date)
    rows = (
        Ride.objects.filter(status=RideStatus.COMPLETED, completed_at__gte=since, completed_at__lt=until)
        .values("captain_id", "captain__user__phone", "captain__user__first_name", "captain__user__last_name")
        .annotate(rides=Count("id"), fares=Sum("final_fare"), platform=Sum("platform_share_amount"))
        .order_by("-fares")
    )
    zero = Decimal("0")
    return [
        {
            "captain_id": row["captain_id"],
            "phone": row["captain__user__phone"],
            "name": f"{row['captain__user__first_name']} {row['captain__user__last_name']}".strip(),
            "completed_rides": row["rides"],
            "fare_total": str(row["fares"] or zero),
            "platform_share": str(row["platform"] or zero),
            "net_earnings": str((row["fares"] or zero) - (row["platform"] or zero)),
        }
        for row in rows
    ]


def to_csv(rows, columns=None):
    """Rows (list of dicts) as CSV text. Values starting with =, +, - or @ are quoted against formula injection."""
    if not rows:
        return ""
    columns = columns or list(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in rows:
        values = []
        for column in columns:
            value = "" if row.get(column) is None else str(row.get(column))
            if value[:1] in ("=", "+", "@") or (value[:1] == "-" and not _is_number(value)):
                value = "'" + value
            values.append(value)
        writer.writerow(values)
    return buffer.getvalue()


def _is_number(value):
    try:
        Decimal(value)
        return True
    except Exception:  # noqa: BLE001
        return False
