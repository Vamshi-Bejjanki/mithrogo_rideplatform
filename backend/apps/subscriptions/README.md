# subscriptions

Captain plans: a 12-hour daily session (Bike ₹30, Auto ₹50), or ride-share (only 1 ride's fare a day, from the first 5).

- Models: `SubscriptionPlan` (name, plan_type, amount, vehicle_type, duration_hours, qualifying_rides, is_active), `CaptainSubscription`, `RideShareDay`, `PlatformDue`
- Statuses: PENDING, ACTIVE, EXPIRED, CANCELLED, FAILED
- Plan types: `DAILY_FLAT`, `RIDE_SHARE`
- Daily plans: `DAILY_BIKE` (₹30, Bike) and `DAILY_AUTO` (₹50, Auto), each lasting 12 hours from payment confirmation. Charged only when the captain buys a session; nothing renews automatically. Buying requires a verified vehicle of the plan's type
- Ride-share plans: `RIDE_SHARE_BIKE` (shortfall ₹30) and `RIDE_SHARE_AUTO` (shortfall ₹50). Plans are per vehicle and the captain only sees plans for the vehicle they chose today.
- Captain chooses a vehicle once per service day (`captains/vehicle-of-day/`). Going online and taking rides need that choice; the active plan must match it.
- Amounts and qualifying-ride counts come from the DB, never hard-coded
- Ride-share: only 1 ride's fare per day goes to the platform, from the captain's first 5 completed rides. Captain may surrender one of the first 4; otherwise the 5th is taken automatically. All other rides that day are free (even 100 rides)
- Counting runs inside ride completion with a row lock on the day's `RideShareDay`
- Shortfall day (1 to 4 rides, none surrendered): next day the captain owes a ₹30 `SHORTFALL_FEE` (blocks going online until paid) and the first ride of that day is taken as a penalty ride. Zero-ride days are exempt
- The periodic job closes ride-share days and applies shortfall penalties
- Cash platform rides create a `PlatformDue`; dues over the limit block going online
- Eligibility check used by go-online and ride accept
- Expiry and day-closing run in `python manage.py run_periodic_jobs` (no Celery yet)
- Expiry never cancels a ride already in progress
- Plan codes: `DAILY_BIKE`, `DAILY_AUTO`, `RIDE_SHARE_BIKE`, `RIDE_SHARE_AUTO`
- APIs: `captains/subscription/` (+ `plans/`, `create-payment/`, `verify-payment/`, `plan/`, `history/`, `dues/`, `dues/pay/`), `captains/rides/{id}/surrender/`. Paying from the wallet is in `wallets/`
