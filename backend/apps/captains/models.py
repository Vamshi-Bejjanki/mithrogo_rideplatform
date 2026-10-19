from django.conf import settings
from django.db import models

from apps.vehicles.models import VehicleType
from core.models import TimeStampedModel


class KycStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    UNDER_REVIEW = "UNDER_REVIEW", "Under review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    SUSPENDED = "SUSPENDED", "Suspended"


class OnlineStatus(models.TextChoices):
    OFFLINE = "OFFLINE", "Offline"
    ONLINE = "ONLINE", "Online"
    BUSY = "BUSY", "Busy"


class CaptainProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="captain_profile")
    profile_photo = models.FileField(upload_to="captains/photos/", blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    license_number = models.CharField(max_length=40, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    kyc_status = models.CharField(max_length=20, choices=KycStatus.choices, default=KycStatus.PENDING, db_index=True)
    kyc_rejection_reason = models.CharField(max_length=300, blank=True, help_text="Shown to the captain.")
    online_status = models.CharField(
        max_length=10, choices=OnlineStatus.choices, default=OnlineStatus.OFFLINE, db_index=True
    )
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_at = models.DateTimeField(null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_rides = models.PositiveIntegerField(default=0)
    cancelled_rides = models.PositiveIntegerField(default=0, help_text="Rides this captain cancelled after accepting.")
    day_vehicle_type = models.CharField(
        max_length=10, choices=VehicleType.choices, null=True, blank=True, help_text="Vehicle chosen for the day."
    )
    day_vehicle_date = models.DateField(null=True, blank=True, help_text="Service day the vehicle was chosen for.")

    def __str__(self):
        return f"Captain {self.user.phone}"


class KycDocument(TimeStampedModel):
    class DocType(models.TextChoices):
        DRIVING_LICENSE = "DRIVING_LICENSE", "Driving licence"
        VEHICLE_REGISTRATION = "VEHICLE_REGISTRATION", "Vehicle registration"
        IDENTITY = "IDENTITY", "Identity proof"
        PHOTO = "PHOTO", "Profile photo"
        OTHER = "OTHER", "Other"

    captain = models.ForeignKey(CaptainProfile, on_delete=models.CASCADE, related_name="kyc_documents")
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    file = models.FileField(upload_to="kyc/%Y/%m/")

    def __str__(self):
        return f"{self.get_doc_type_display()} ({self.captain.user.phone})"
