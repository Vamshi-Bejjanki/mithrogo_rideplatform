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


class TicketMessage(models.Model):
    """One message in a ticket's conversation, from the user or from support staff."""

    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    is_staff = models.BooleanField(default=False)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{'Support' if self.is_staff else 'User'} on ticket {self.ticket_id}"


class SosStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
    RESOLVED = "RESOLVED", "Resolved"


class SosAlert(models.Model):
    """An emergency raised from an app. Every admin is alerted at once."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sos_alerts")
    ride = models.ForeignKey("rides.Ride", null=True, blank=True, on_delete=models.SET_NULL, related_name="sos_alerts")
    ticket = models.OneToOneField(SupportTicket, null=True, blank=True, on_delete=models.SET_NULL, related_name="sos")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    note = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=14, choices=SosStatus.choices, default=SosStatus.OPEN, db_index=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"SOS {self.pk} ({self.status})"
