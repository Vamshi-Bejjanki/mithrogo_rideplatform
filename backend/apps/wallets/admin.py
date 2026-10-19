from django.contrib import admin

from apps.wallets.models import CaptainWallet, WalletTransaction


@admin.register(CaptainWallet)
class CaptainWalletAdmin(admin.ModelAdmin):
    list_display = ("captain", "balance", "updated_at")
    search_fields = ("captain__user__phone",)
    readonly_fields = ("balance", "created_at", "updated_at")
    raw_id_fields = ("captain",)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "kind", "amount", "balance_after", "reference", "created_at")
    list_filter = ("kind",)
    search_fields = ("reference", "wallet__captain__user__phone")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
