# wallets

Captain wallet: a prepaid balance captains use to pay Mithrogo for plans and platform dues. Customers pay captains in cash, so there is no customer wallet.

- Models: `CaptainWallet` (balance, one per captain), `WalletTransaction` (append-only ledger; unique per kind + reference so nothing is charged twice)
- Money in: top-up through the payment gateway (`PaymentType.WALLET_TOP_UP`). Credited only when the webhook confirms the payment
- Money out: `pay-plan/` (daily plan, activates at once) and `pay-dues/` (all pending dues, settled in one step). Both fail rather than going negative
- No withdrawals in this version
