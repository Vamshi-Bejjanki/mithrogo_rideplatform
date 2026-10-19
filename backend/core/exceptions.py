from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class DomainError(Exception):
    """A business rule was violated. Services raise these; the API turns them into JSON errors."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail, code="invalid"):
        super().__init__(detail)
        self.detail = str(detail)
        self.code = code


class Conflict(DomainError):
    status_code = status.HTTP_409_CONFLICT


class Forbidden(DomainError):
    status_code = status.HTTP_403_FORBIDDEN


class RateLimited(DomainError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


def api_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response({"detail": exc.detail, "code": exc.code}, status=exc.status_code)
    return drf_exception_handler(exc, context)
