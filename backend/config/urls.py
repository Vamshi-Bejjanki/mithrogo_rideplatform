from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import api_index, health
from apps.rides.views import SharedTripView

api_v1 = [
    path("", api_index, name="api-index"),
    path("health/", health, name="health"),
    path("auth/", include("apps.users.urls")),
    path("customers/", include("apps.customers.urls")),
    path("captains/vehicles/", include("apps.vehicles.urls")),
    path("captains/subscription/", include("apps.subscriptions.urls")),
    path("captains/wallet/", include("apps.wallets.urls")),
    path("captains/", include("apps.captains.urls")),
    path("captains/", include("apps.rides.captain_urls")),
    path("rides/", include("apps.rides.urls")),
    path("payments/", include("apps.payments.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("support/", include("apps.support.urls")),
    path("share/<str:token>/", SharedTripView.as_view(), name="shared-trip"),
    path("admin/", include("apps.backoffice.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
