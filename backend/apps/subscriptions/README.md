# subscriptions

Captain plans: ₹30 daily subscription or ride-share (only 1 ride's fare a day, from the first 5).

- Models: `SubscriptionPlan` (name, plan_type, amount, duration_days, qualifying_rides, is_active), `CaptainSubscription`, `RideShareDay`, `PlatformDue`
- Statuses: PENDING, ACTIVE, EXPIRED, CANCELLED, FAILED
- Plan types: `DAILY_FLAT`, `RIDE_SHARE`
- Initial plans: `DAILY_30` (₹30 / 1 day) and `RIDE_SHARE_1_IN_5` — amount and qualifying-ride count come from DB, never hard-coded
- Ride-share: only 1 ride's fare per day goes to the platform, from the captain's first 5 completed rides. Captain may surrender one of the first 4; otherwise the 5th is taken automatically. All other rides that day are free (even 100 rides)
- Counting runs inside ride completion with a row lock on the day's `RideShareDay`
- Shortfall day (1 to 4 rides, none surrendered): next day the captain owes a ₹30 `SHORTFALL_FEE` (blocks going online until paid) and the first ride of that day is taken as a penalty ride. Zero-ride days are exempt
- End-of-day Celery job closes days and applies shortfall penalties
- Cash platform rides create a `PlatformDue`; dues over the limit block going online
- Eligibility check used by go-online and ride accept
- Celery task to expire subscriptions
- Expiry never cancels a ride already in progress
- APIs: `/captains/subscription/`, `create-payment/`, `verify-payment/`, plan switch, `/captains/rides/{id}/surrender/`, dues
