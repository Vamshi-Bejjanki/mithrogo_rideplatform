from django.conf import settings
from django.db import models


class TicketCategory(models.TextChoices):
    RIDE_ISSUE = "RIDE_ISSUE", "Issue with a ride"
    PAYMENT = "PAYMENT", "Payment or fare"
    SAFETY = "SAFETY", "Safety"
    ACCOUNT = "ACCOUNT", "Account or documents"
    OTHER = "OTHER", "Other"


class TicketStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    RESOLVED = "RESOLVED", "Resolved"
    CLOSED = "CLOSED", "Closed"


class SupportTicket(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_tickets")
    ride = models.ForeignKey("rides.Ride", null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets")
    category = models.CharField(max_length=20, choices=TicketCategory.choices)
    description = models.TextField()
    status = models.CharField(max_length=12, choices=TicketStatus.choices, default=TicketStatus.OPEN, db_index=True)
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket {self.pk} ({self.get_category_display()})"
