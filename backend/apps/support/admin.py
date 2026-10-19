from django import forms
from django.contrib import admin
from django.utils.html import format_html

from core import audit
from core.admin import AuditedModelAdmin, ReasonActionForm, action_reason, csv_export_action, run_action
from apps.support import services
from apps.support.models import SosAlert, SosStatus, SupportTicket, TicketMessage, TicketStatus


def _set_status(new_status, request=None):
    def handler(ticket, actor):
        services.set_ticket_status(ticket, new_status, action_reason(request) if request else "", actor)

    return handler


class TicketMessageInline(admin.TabularInline):
    """The conversation, oldest first. Read-only; reply with the box above."""

    model = TicketMessage
    extra = 0
    can_delete = False
    fields = ("created_at", "sender", "body")
    readonly_fields = fields
    verbose_name_plural = "Conversation"

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="From")
    def sender(self, message):
        if message.is_staff:
            name = message.author.full_name if message.author else ""
            return format_html("<b>Support</b> {}", f"({name})" if name else "")
        return message.author.phone if message.author else "User"


class TicketAdminForm(forms.ModelForm):
    reply = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "cols": 80}),
        help_text="Sent to the user in the app (and by push). Saving with a reply moves an open ticket to in progress.",
    )

    class Meta:
        model = SupportTicket
        fields = ("status", "resolution_note")


@admin.register(SupportTicket)
class SupportTicketAdmin(AuditedModelAdmin):
    form = TicketAdminForm
    list_display = ("id", "user", "category", "ride", "status", "is_sos", "created_at", "updated_at")
    list_filter = ("status", "category")
    search_fields = ("user__phone", "description", "ride__id")
    readonly_fields = ("user", "ride", "category", "description", "created_at", "updated_at")
    fields = ("user", "ride", "category", "description", "status", "resolution_note", "reply", "created_at",
              "updated_at")
    inlines = [TicketMessageInline]
    action_form = ReasonActionForm
    actions = ["mark_in_progress", "mark_resolved", "export_csv"]
    export_csv = csv_export_action(
        [("id", "id"), ("user", "user__phone"), ("category", "category"), ("status", "status"),
         ("ride", "ride_id"), ("description", "description"), ("created_at", "created_at")],
        "tickets",
    )

    @admin.display(boolean=True, description="SOS")
    def is_sos(self, ticket):
        return hasattr(ticket, "sos")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        reply = (form.cleaned_data.get("reply") or "").strip()
        if reply:
            services.add_message(obj, request.user, reply, is_staff=True)
            audit.record(request.user, "admin.ticket_reply", obj)

    @admin.action(description="Mark selected tickets in progress")
    def mark_in_progress(self, request, queryset):
        run_action(
            self, request, queryset, "ticket_in_progress", _set_status(TicketStatus.IN_PROGRESS), "Updated {count} ticket(s)."
        )

    @admin.action(description="Mark selected tickets resolved (optional note in the box)")
    def mark_resolved(self, request, queryset):
        run_action(
            self, request, queryset, "ticket_resolved", _set_status(TicketStatus.RESOLVED, request),
            "Resolved {count} ticket(s).",
        )


@admin.register(SosAlert)
class SosAlertAdmin(admin.ModelAdmin):
    list_display = ("id", "status_badge", "user", "ride", "created_at", "handled_by", "acknowledged_at")
    list_filter = ("status",)
    search_fields = ("user__phone", "note")
    readonly_fields = ("user", "ride", "ticket", "location", "latitude", "longitude", "note", "status", "handled_by",
                       "acknowledged_at", "resolved_at", "resolution_note", "created_at")
    action_form = ReasonActionForm
    actions = ["acknowledge", "resolve"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Status")
    def status_badge(self, alert):
        color = {"OPEN": "#c62828", "ACKNOWLEDGED": "#f57c00", "RESOLVED": "#2e7d32"}[alert.status]
        return format_html('<b style="color:{}">{}</b>', color, alert.get_status_display())

    @admin.display(description="Map")
    def location(self, alert):
        if alert.latitude is None:
            return "No location sent."
        url = f"https://www.openstreetmap.org/?mlat={alert.latitude}&mlon={alert.longitude}#map=17/{alert.latitude}/{alert.longitude}"
        return format_html('<a href="{}" target="_blank">Open location on map</a>', url)

    @admin.action(description="Acknowledge (tells the user help is coming)")
    def acknowledge(self, request, queryset):
        run_action(self, request, queryset.filter(status=SosStatus.OPEN), "acknowledge_sos",
                   lambda alert, actor: services.acknowledge_sos(alert, actor), "Acknowledged {count} alert(s).")

    @admin.action(description="Resolve (note in the box)")
    def resolve(self, request, queryset):
        note = action_reason(request)
        run_action(self, request, queryset.exclude(status=SosStatus.RESOLVED), "resolve_sos",
                   lambda alert, actor: services.resolve_sos(alert, actor, note), "Resolved {count} alert(s).")
