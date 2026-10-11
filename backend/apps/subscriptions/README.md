# subscriptions

Captain daily platform subscription.

- Models: `SubscriptionPlan` (name, amount, duration_days, is_active), `CaptainSubscription`
- Statuses: PENDING, ACTIVE, EXPIRED, CANCELLED, FAILED
- Initial plan `DAILY_20` (₹20 / 1 day) — amount comes from DB, never hard-coded
- Eligibility check used by go-online and ride accept
- Celery task to expire subscriptions
- Expiry never cancels a ride already in progress
- APIs: `/captains/subscription/`, `create-payment/`, `verify-payment/`
