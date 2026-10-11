# payments

`Payment` model and payment-gateway abstraction.

- Types: `RIDE_PAYMENT`, `CAPTAIN_SUBSCRIPTION`
- Statuses: CREATED, PENDING, SUCCESS, FAILED, REFUNDED
- Provider interface with a mock implementation first, real gateway later
- Webhook handling and reconciliation
- Never trust "payment succeeded" from the mobile app; verify with the provider
