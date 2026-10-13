from django.contrib import admin

from core.admin import AuditedModelAdmin, run_action
from apps.support.models import SupportTicket, TicketStatus


def _set_status(new_status):
    def handler(ticket, actor):
        ticket.status = new_status
        ticket.save(update_fields=["status", "updated_at"])

    return handler


@admin.register(SupportTicket)
class SupportTicketAdmin(AuditedModelAdmin):
    list_display = ("id", "user", "category", "ride", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("user__phone", "description", "ride__id")
    readonly_fields = ("user", "ride", "category", "description", "created_at", "updated_at")
    fields = ("user", "ride", "category", "description", "status", "resolution_note", "created_at", "updated_at")
    actions = ["mark_in_progress", "mark_resolved"]

    @admin.action(description="Mark selected tickets in progress")
    def mark_in_progress(self, request, queryset):
        run_action(
            self, request, queryset, "ticket_in_progress", _set_status(TicketStatus.IN_PROGRESS), "Updated {count} ticket(s)."
        )

    @admin.action(description="Mark selected tickets resolved")
    def mark_resolved(self, request, queryset):
        run_action(
            self, request, queryset, "ticket_resolved", _set_status(TicketStatus.RESOLVED), "Resolved {count} ticket(s)."
        )
