from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import health

api_v1 = [
    path("health/", health, name="health"),
    path("auth/", include("apps.users.urls")),
    path("customers/", include("apps.customers.urls")),
    path("captains/vehicles/", include("apps.vehicles.urls")),
    path("captains/subscription/", include("apps.subscriptions.urls")),
    path("captains/", include("apps.captains.urls")),
    path("captains/", include("apps.rides.captain_urls")),
    path("rides/", include("apps.rides.urls")),
    path("payments/", include("apps.payments.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("support/", include("apps.support.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
