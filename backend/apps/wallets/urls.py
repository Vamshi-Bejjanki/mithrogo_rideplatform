from django.urls import path

from apps.wallets.views import WalletPayDuesView, WalletPayPlanView, WalletTopUpView, WalletView

urlpatterns = [
    path("", WalletView.as_view(), name="captain-wallet"),
    path("top-up/", WalletTopUpView.as_view(), name="captain-wallet-top-up"),
    path("pay-plan/", WalletPayPlanView.as_view(), name="captain-wallet-pay-plan"),
    path("pay-dues/", WalletPayDuesView.as_view(), name="captain-wallet-pay-dues"),
]
