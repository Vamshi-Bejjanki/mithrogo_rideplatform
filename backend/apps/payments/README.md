# payments

`Payment` model and payment-gateway abstraction (`providers.py`).

- Types include `RIDE_PAYMENT`, `CAPTAIN_SUBSCRIPTION`, `WALLET_TOP_UP`, and payments for dues and cancellation fees
- Statuses: CREATED, PENDING, SUCCESS, FAILED, REFUNDED
- Only a mock provider exists (`PAYMENT_PROVIDER`); a real gateway is a new provider class
- The webhook (`payments/webhook/`) needs a valid HMAC `X-Payment-Signature`. `services.mark_success` is idempotent and checks the amount
- Never trust "payment succeeded" from the app. `payments/{id}/` only reports status
- Dev: `python manage.py simulate_payment <provider_order_id>` (debug only)
