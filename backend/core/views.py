from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_index(request):
    """Lists the top-level API sections so the bare /api/v1/ URL is useful."""
    return Response(
        {
            "health": "health/",
            "auth": "auth/",
            "customers": "customers/",
            "captains": "captains/",
            "vehicles": "captains/vehicles/",
            "subscription": "captains/subscription/",
            "rides": "rides/",
            "payments": "payments/",
            "notifications": "notifications/",
            "support": "support/",
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Liveness plus a database round-trip."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return Response({"status": "ok"})
