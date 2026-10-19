from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    profile_photo = models.FileField(upload_to="customers/photos/", blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=80, blank=True)
    emergency_contact_phone = models.CharField(max_length=16, blank=True)
    referral_code = models.CharField(max_length=12, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="referrals"
    )
    referral_rewarded_at = models.DateTimeField(
        null=True, blank=True, help_text="When the referrer was rewarded for this rider's first ride."
    )

    def __str__(self):
        return f"Customer {self.user.phone}"


class PlaceLabel(models.TextChoices):
    HOME = "HOME", "Home"
    WORK = "WORK", "Work"
    OTHER = "OTHER", "Other"


class SavedPlace(TimeStampedModel):
    """A rider's saved pickup or drop point. One Home and one Work per rider; any number of others."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_places")
    label = models.CharField(max_length=10, choices=PlaceLabel.choices, default=PlaceLabel.OTHER)
    name = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        ordering = ["label", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "label"],
                condition=~models.Q(label="OTHER"),
                name="one_home_and_one_work_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.get_label_display()}: {self.name}"
