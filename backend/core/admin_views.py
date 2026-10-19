"""Custom Django Admin pages: live map, reports (with CSV), and broadcast announcements."""

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from core import reports
from core.models import AuditLog


def live_map(site, request):
    context = {**site.each_context(request), "title": "Live map"}
    return TemplateResponse(request, "core/admin/live_map.html", context)


def live_map_data(site, request):
    """JSON for the live map: active rides and online/busy captains. Polled by the page every few seconds."""
    from apps.captains.models import CaptainProfile
    from apps.rides.models import ACTIVE_STATUSES, Ride

    def num(value):
        return float(value) if value is not None else None

    rides = [
        {
            "id": str(ride.id),
            "url": f"/admin/rides/ride/{ride.id}/change/",
            "status": ride.status,
            "vehicle_type": ride.vehicle_type,
            "customer": ride.customer.phone,
            "captain": ride.captain.user.phone if ride.captain_id else None,
            "pickup": [num(ride.pickup_latitude), num(ride.pickup_longitude)],
            "drop": [num(ride.drop_latitude), num(ride.drop_longitude)],
            "pickup_address": ride.pickup_address,
            "drop_address": ride.drop_address,
        }
        for ride in Ride.objects.filter(status__in=ACTIVE_STATUSES).select_related("customer", "captain__user")
    ]
    captains = [
        {
            "id": c.pk,
            "url": f"/admin/captains/captainprofile/{c.pk}/change/",
            "name": c.user.full_name or c.user.phone,
            "status": c.online_status,
            "position": [num(c.current_latitude), num(c.current_longitude)],
            "updated_at": c.last_location_at.isoformat() if c.last_location_at else None,
        }
        for c in CaptainProfile.objects.filter(
            online_status__in=["ONLINE", "BUSY"], current_latitude__isnull=False
        ).select_related("user")
    ]
    return JsonResponse({"rides": rides, "captains": captains})


def reports_view(site, request):
    if not request.user.has_perm("payments.view_payment"):
        raise PermissionDenied
    start, end = reports.parse_range(request.GET.get("from"), request.GET.get("to"))
    kind = request.GET.get("report", "daily")
    rows = reports.captain_earnings_report(start, end) if kind == "earnings" else reports.daily_report(start, end)
    if request.GET.get("export") == "csv":
        AuditLog.objects.create(actor=request.user, action="admin.export_report", model="core.report",
                                object_id=kind, changes={"from": str(start), "to": str(end)})
        response = HttpResponse(reports.to_csv(rows), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{kind}-{start}-to-{end}.csv"'
        return response
    columns = list(rows[0].keys()) if rows else []
    context = {
        **site.each_context(request),
        "title": "Reports",
        "kind": kind,
        "start": start,
        "end": end,
        "columns": columns,
        "table": [[row.get(c) for c in columns] for row in rows],
        "totals": reports.report_totals(rows) if kind == "daily" else None,
        "chart": _chart(rows) if kind == "daily" else None,
    }
    return TemplateResponse(request, "core/admin/reports.html", context)


def _chart(rows):
    """Bar heights (0-100) for completed rides and gross fares per day, for a simple CSS chart."""
    if not rows:
        return []
    max_rides = max(r["rides_completed"] for r in rows) or 1
    max_fares = max(float(r["gross_fares"]) for r in rows) or 1
    return [
        {
            "date": r["date"][5:],
            "rides": r["rides_completed"],
            "fares": r["gross_fares"],
            "rides_pct": round(r["rides_completed"] * 100 / max_rides),
            "fares_pct": round(float(r["gross_fares"]) * 100 / max_fares),
        }
        for r in rows
    ]


class BroadcastForm(forms.Form):
    audience = forms.ChoiceField(choices=[("CUSTOMERS", "All customers"), ("CAPTAINS", "All captains"),
                                          ("ALL", "Everyone")])
    title = forms.CharField(max_length=120)
    message = forms.CharField(max_length=500, widget=forms.Textarea(attrs={"rows": 4, "cols": 60}))


def broadcast_view(site, request):
    from apps.notifications.services import notify
    from apps.users.models import Role, User

    if not request.user.has_perm("notifications.add_notification"):
        raise PermissionDenied
    form = BroadcastForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        roles = {"CUSTOMERS": [Role.CUSTOMER], "CAPTAINS": [Role.CAPTAIN], "ALL": [Role.CUSTOMER, Role.CAPTAIN]}
        count = 0
        for user in User.objects.filter(role__in=roles[data["audience"]], is_active=True).iterator():
            notify(user, "ANNOUNCEMENT", data["title"], data["message"])
            count += 1
        AuditLog.objects.create(actor=request.user, action="admin.broadcast", model="notifications.notification",
                                object_id="-", changes={**data, "recipients": count})
        messages.success(request, f"Sent to {count} user(s).")
        return redirect("admin:broadcast")
    context = {**site.each_context(request), "title": "Send announcement", "form": form}
    return TemplateResponse(request, "core/admin/broadcast.html", context)
