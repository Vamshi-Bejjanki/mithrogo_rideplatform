from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from core.exceptions import DomainError
from apps.users import otp
from apps.users.serializers import LogoutSerializer, SendOtpSerializer, UserSerializer, VerifyOtpSerializer
from apps.users.services import login_for_role
from apps.users.tokens import issue_tokens


class SendOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp.issue_otp(serializer.validated_data["phone"])
        return Response({"detail": "Code sent."}, status=status.HTTP_200_OK)


class VerifyOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        otp.verify_otp(data["phone"], data["code"])
        user = login_for_role(data["phone"], data["role"])
        return Response({"user": UserSerializer(user).data, **issue_tokens(user)})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
        except TokenError:
            raise DomainError("The session is already invalid.", code="invalid_token")
        if str(token.get("user_id")) != str(request.user.id):
            raise DomainError("This token does not belong to you.", code="invalid_token")
        token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
