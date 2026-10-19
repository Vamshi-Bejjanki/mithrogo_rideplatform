from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import AdminLoginView, DeleteAccountView, LogoutView, MeView, SendOtpView, VerifyOtpView

urlpatterns = [
    path("send-otp/", SendOtpView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOtpView.as_view(), name="verify-otp"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("delete-account/", DeleteAccountView.as_view(), name="delete-account"),
    path("admin/login/", AdminLoginView.as_view(), name="admin-login"),
]
