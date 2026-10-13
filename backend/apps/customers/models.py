from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    profile_photo = models.FileField(upload_to="customers/photos/", blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=80, blank=True)
    emergency_contact_phone = models.CharField(max_length=16, blank=True)

    def __str__(self):
        return f"Customer {self.user.phone}"
