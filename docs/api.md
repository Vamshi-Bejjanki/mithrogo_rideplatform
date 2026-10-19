# API reference (MVP)

Base URL: `/api/v1/` (for example `http://127.0.0.1:8000/api/v1/` in development).

## Conventions

- **Auth:** send `Authorization: Bearer <access token>`. Get the tokens from `auth/verify-otp/`. Access tokens last 30 minutes; refresh with `auth/refresh/`.
- **Money:** amounts are strings with two decimals, for example `"62.72"`.
- **Errors:** `{"detail": "message", "code": "machine_code"}`. Validation errors on a field use DRF's standard format.
- **Status codes:** `400` invalid input or rule violated, `401` not signed in, `403` wrong role or not allowed, `404` not found (also used when a record belongs to someone else), `409` the action conflicts with the current state, `429` too many attempts.
- **Coordinates:** latitude and longitude as decimal strings, for example `"18.672500"`.
- **Idempotency:** `POST rides/` accepts an optional `Idempotency-Key` header. Repeating the same key returns the same ride.

## Auth and health

| Method | Path | Auth | Body / notes |
|---|---|---|---|
| GET | `health/` | none | Returns `{"status": "ok"}` when the database responds. |
| POST | `auth/send-otp/` | none | `{"phone": "+919900000001"}`. Sends a 6-digit code by SMS. Returns `{"detail": "Code sent."}`. Max 5 codes per phone per hour. |
| POST | `auth/verify-otp/` | none | `{"phone": "...", "code": "123456", "role": "CUSTOMER"}`, or `"CAPTAIN"`. Returns `user`, `access`, `refresh`. Codes expire after 5 minutes, work once, and lock after 5 wrong tries. |
| POST | `auth/refresh/` | none | `{"refresh": "..."}`. Returns new tokens and rotates the refresh token. |
| POST | `auth/logout/` | bearer | `{"refresh": "..."}`. Blacklists the refresh token. Returns `204`. |
| GET | `auth/me/` | bearer | Current user. |
| GET | `auth/delete-account/` | bearer | `{"can_delete": bool, "reasons": [...]}`. Blocked during an active ride, with unpaid fees, or (captains) with dues or wallet money. |
| POST | `auth/delete-account/` | bearer | `{"confirm": true, "reason"?}`. Anonymises the account (rides and payments are kept for records), frees the phone number, and ends every session. Returns `204`. |
| POST | `auth/admin/login/` | none | `{"phone", "password"}`. Admin web app login. Only active `ADMIN` accounts get tokens. |

A phone number belongs to one role. A captain's number can't sign in with `"role": "CUSTOMER"`, and the reverse.

## Customer

| Method | Path | Body / notes |
|---|---|---|
| GET, PATCH | `customers/profile/` | PATCH fields: `first_name`, `last_name`, `email`, `emergency_contact_name`, `emergency_contact_phone`. |
| GET, POST | `customers/places/` | Saved places. POST: `{"label": "HOME"\|"WORK"\|"OTHER", "name", "address", "latitude", "longitude"}`. One HOME and one WORK (`409 place_exists`), up to 20 others. |
| GET, PATCH, DELETE | `customers/places/{id}/` | One saved place. |
| GET | `customers/promos/` | Promo codes this rider can use: public ones and personal referral rewards. |
| GET | `customers/referral/` | `referral_code`, `referred_count`, `rewarded_count`, reward amounts, and whether referrals are running. |
| POST | `customers/referral/apply/` | `{"code"}`. Once per rider, before their first completed ride. Returns the welcome reward code, if any. |

## Rides (customer)

| Method | Path | Body / notes |
|---|---|---|
| POST | `rides/estimate/` | `{"vehicle_type": "BIKE", "pickup_latitude", "pickup_longitude", "drop_latitude", "drop_longitude", "promo_code"?}`. Returns `distance_km`, `duration_minutes`, `fare`, `discount`, `payable_fare`, `currency`. Stores nothing. |
| GET | `rides/` | The 50 most recent rides. |
| POST | `rides/` | Estimate fields plus `pickup_address`, `drop_address`, `payment_method` (`ONLINE` or `CASH`, default `ONLINE`), `promo_code`?. Optional `Idempotency-Key` header. Starts matching immediately. Refused with `409 unpaid_cancellation_fee` while a fee is owed. |
| GET | `rides/{id}/` | Ride details, including `start_pin` (until the trip starts), `payable_fare`, `discount_amount`, cancellation fields, `is_rated` and `my_rating`. Also moves a stalled search forward. |
| GET | `rides/{id}/cancel/` | Preview: `can_cancel`, the `fee` cancelling now would cost, `free_until`, and the `reasons` to choose from. |
| POST | `rides/{id}/cancel/` | `{"reason": "CHANGED_MIND"\|"CAPTAIN_DELAYED"\|"WRONG_PICKUP"\|"CAPTAIN_ASKED"\|"FOUND_OTHER_RIDE"\|"SAFETY"\|"OTHER", "note"?}`. Allowed until the ride starts. A fee applies only after a captain accepted and the free window passed, and never for `CAPTAIN_ASKED` or `SAFETY`. |
| GET | `rides/outstanding-fees/` | Cancelled rides whose fee is still unpaid. |
| POST | `rides/{id}/fee-payment/` | Creates an online payment for the ride's cancellation or no-show fee. Once paid, the fee goes to the captain's wallet. |
| GET | `rides/{id}/tracking/` | Ride status, pickup and drop, `start_pin`, and the captain's latest location and vehicle once a captain has accepted. |
| POST, DELETE | `rides/{id}/share/` | POST returns `{"token", "url"}`: a public link to follow the trip. DELETE stops sharing. Active rides only. |
| GET | `share/{token}/` | **Public, no login.** Status, rider first name, pickup and drop, and the captain's name, plate and live location while the ride is in progress. No phone numbers or PIN. Stops working a while after the ride ends. |
| POST | `rides/{id}/payment/` | Creates an online payment for a completed `ONLINE` ride, for the `payable_fare` (after any promo). Returns a payment with `provider_order_id`. |
| POST | `rides/{id}/rating/` | `{"rating": 1-5, "comment": "..."}`. Only for completed rides, once per ride. |

**Ride start PIN.** Every ride gets a 4-digit PIN that only the rider sees. The captain must send it to `captains/rides/{id}/start/`. Wrong PINs are limited per ride (`429 pin_locked`). Admins can turn PINs off in Platform configuration.

**Promo codes** are funded by the platform. The captain earns the full fare; for cash rides the discount is credited to the captain's wallet when the ride completes.

A customer can have only one active ride at a time. The fare is fixed when the ride is created. The client cannot change it.

## Captain profile, status, and location

| Method | Path | Body / notes |
|---|---|---|
| GET, PATCH | `captains/profile/` | PATCH fields: `date_of_birth`, `address`. Status fields are read-only. |
| GET | `captains/status/` | `eligible`, `reasons`, and a plain-language `message`. Use it to show why a captain can't go online. |
| POST | `captains/status/online/` | Fails with `403` and the reason if the captain isn't eligible. |
| POST | `captains/status/offline/` | Fails with `409` while on a ride. |
| GET | `captains/wallet/` | Captain wallet balance and last 20 transactions. Only captains have a wallet. Customers pay captains in cash. |
| POST | `captains/wallet/top-up/` | `{"amount": "100.00"}` (min ₹1). Creates a gateway payment. The balance rises only when the webhook confirms it. |
| POST | `captains/wallet/pay-plan/` | `{"plan_code": "DAILY_BIKE"}`. Buys a daily plan from the wallet and activates it at once. Fails with `insufficient_balance`. |
| POST | `captains/wallet/pay-dues/` | Settles all pending platform dues from the wallet. Fails with `no_dues` if nothing is owed. |
| POST | `captains/vehicle-of-day/` | `{"vehicle_type": "BIKE" or "AUTO"}`. Choose the vehicle worked with today. Needed once per service day before going online or taking rides. The vehicle must be verified. Allowed while online, not mid-ride. |
| POST | `captains/location/` | `{"latitude", "longitude", "heading"?, "speed"?}`. Returns `204`. Locations older than 30 seconds are not used for matching. |
| POST | `captains/kyc/` | `{"license_number", "license_expiry", "date_of_birth"?, "address"?}`. Needs at least one uploaded document. Locked after approval. |
| POST | `captains/kyc/documents/` | Multipart form: `doc_type` (`DRIVING_LICENSE`, `VEHICLE_REGISTRATION`, `IDENTITY`, `PHOTO`, `OTHER`) and `file`. |
| GET | `captains/kyc/documents/` | Documents uploaded so far. |
| GET, POST | `captains/vehicles/` | POST: `{"vehicle_type": "BIKE"\|"AUTO", "registration_number", "make"?, "model"?, "color"?}`. One vehicle per type. New vehicles are unverified until an admin verifies them. |
| GET | `captains/earnings/` | `completed_rides`, `fare_total`, `platform_share`, `net_earnings`, today's totals, and `pending_dues`. |

## Ride requests and rides (captain)

| Method | Path | Body / notes |
|---|---|---|
| GET | `captains/offers/` | Open ride requests for this captain. Each one expires after the offer timeout (15 seconds by default). |
| POST | `captains/rides/{id}/accept/` | Captain must be online and have an open request for this ride. Fails with `409` if the offer expired or another captain took the ride. |
| POST | `captains/rides/{id}/reject/` | Passes the request to the next nearest captain. |
| POST | `captains/rides/{id}/arrived/` | `ACCEPTED` → `CAPTAIN_ARRIVED`. |
| POST | `captains/rides/{id}/start/` | `{"pin": "1234"}`, the rider's PIN. `CAPTAIN_ARRIVED` → `STARTED`. Fails with `pin_required`, `wrong_pin`, or `429 pin_locked`. |
| POST | `captains/rides/{id}/cancel/` | `{"reason": "CUSTOMER_NOT_AT_PICKUP"\|"CUSTOMER_ASKED"\|"VEHICLE_ISSUE"\|"PICKUP_UNREACHABLE"\|"SAFETY"\|"OTHER", "note"?}`. Before the trip starts. A rider no-show (after waiting at pickup) or rider request cancels the ride; a no-show fee may apply. Any other reason sends the ride back to searching for the next captain, and counts on the captain's record. |
| POST | `captains/rides/{id}/complete/` | `STARTED` → `COMPLETED`. Updates earnings and the ride-share count. |
| POST | `captains/rides/{id}/surrender/` | Ride-share plan only. Marks this ride as the platform ride, if it's one of the first four rides today. Once per day. |
| POST | `captains/rides/{id}/collect-cash/` | For completed `CASH` rides. Records the cash as collected. |
| GET | `captains/rides/` | Optional `?status=COMPLETED`. The 50 most recent rides. |
| GET | `captains/rides/{id}/` | Details of one of this captain's rides. |

Ride status flow: `REQUESTED` → `SEARCHING` → `ACCEPTED` → `CAPTAIN_ARRIVED` → `STARTED` → `COMPLETED`. `CANCELLED` is reachable before the ride starts. A captain cancellation moves `ACCEPTED` or `CAPTAIN_ARRIVED` back to `SEARCHING`. Invalid moves return `409 invalid_transition`.

## Captain plans and dues

| Method | Path | Body / notes |
|---|---|---|
| GET | `captains/subscription/` | Current plan, `eligible`, `reasons`, `pending_dues`, and today's ride-share progress. |
| GET | `captains/subscription/plans/` | Active plans with their current prices. |
| POST | `captains/subscription/create-payment/` | `{"plan_code": "DAILY_BIKE"}` or `DAILY_AUTO` (ride-share: `RIDE_SHARE_BIKE` / `RIDE_SHARE_AUTO`). Creates a payment. The vehicle type must have a verified vehicle. The plan activates only after the gateway confirms it. |
| POST | `captains/subscription/verify-payment/` | `{"payment_id": "..."}`. Reports status only. It never activates a plan. |
| POST | `captains/subscription/plan/` | `{"plan_code": "RIDE_SHARE_1_IN_5"}`. Switches to the ride-share plan immediately. Refused while on a ride. |
| GET | `captains/subscription/history/` | Past and current plans. |
| GET | `captains/subscription/dues/` | Platform dues: amounts, types, and status. |
| POST | `captains/subscription/dues/pay/` | Creates one payment covering all pending dues. |

## Payments, notifications, support

| Method | Path | Body / notes |
|---|---|---|
| GET | `payments/{id}/` | Owner only. Shows status. Never activates anything. |
| POST | `payments/webhook/` | Gateway only. Requires a valid `X-Payment-Signature`. Apps must not call this. |
| GET | `notifications/` | The 100 most recent notifications. |
| POST | `notifications/{id}/read/` | Marks one as read. |
| POST | `notifications/read-all/` | Marks all as read. Returns `{"marked_read": n}`. |
| POST, DELETE | `notifications/devices/` | POST `{"token", "platform": "ANDROID"\|"IOS"\|"WEB", "app_version"?}` registers this phone for push. DELETE with `{"token"}` removes it (call on logout). Every notification is also pushed once the change is saved. |
| GET, POST | `support/tickets/` | POST: `{"category": "RIDE_ISSUE"\|"PAYMENT"\|"SAFETY"\|"ACCOUNT"\|"OTHER", "description", "ride_id"?}`. `ride_id` must be a ride the user took part in. |
| GET | `support/tickets/{id}/` | One ticket with its conversation. |
| GET, POST | `support/tickets/{id}/messages/` | The conversation; POST `{"body"}` replies. A reply reopens a resolved ticket. Support replies arrive as `SUPPORT_REPLY` notifications. |
| GET, POST | `support/sos/` | POST `{"latitude"?, "longitude"?, "note"?, "ride_id"?}` raises an SOS. The active ride is attached automatically. Every admin is alerted at once and a SAFETY ticket is opened. Max 5 per minute. GET lists your recent alerts. |

## Admin API (`admin/`)

For the admin web app. Every endpoint needs an `ADMIN` token (`auth/admin/login/`); customers and captains get `403`. Every change is written to the audit log. Lists take `?search=`, field filters, and `?limit=&offset=` (default 50, max 200) and return `{"count", "next", "previous", "results"}`.

| Method | Path | Notes |
|---|---|---|
| GET | `admin/dashboard/` | Live counts and totals, plus the last 7 days. |
| GET | `admin/reports/daily/` | `?from=YYYY-MM-DD&to=YYYY-MM-DD`. Rides and money per day, with totals. Add `&export=csv` for a CSV file. |
| GET | `admin/reports/captain-earnings/` | Same range and CSV option. Per-captain rides, fares, platform share, net. |
| GET | `admin/customers/`, `admin/customers/{id}/` | Filters: `is_active`. |
| POST | `admin/customers/{id}/suspend/`, `.../reactivate/` | |
| GET | `admin/captains/`, `admin/captains/{id}/` | Filters: `kyc_status`, `online_status`. Detail includes vehicles and KYC document links. |
| POST | `admin/captains/{id}/approve/`, `reject/`, `suspend/`, `reactivate/` | `reject` needs `{"reason"}`, which the captain sees. |
| POST | `admin/vehicles/{id}/verify/`, `.../unverify/` | |
| GET | `admin/rides/` | Filters: `status`, `vehicle_type`, `payment_method`, `captain`, `customer`, `from`, `to`. |
| GET | `admin/rides/live/` | Active rides with captain positions, and every captain online. |
| GET | `admin/rides/{id}/` | Full detail: timeline (status events), offers, rating. |
| GET | `admin/rides/{id}/route/` | The captain's recorded location trail. |
| POST | `admin/rides/{id}/cancel/` | `{"reason"}`. |
| POST | `admin/rides/{id}/waive-fee/` | Waives an unpaid cancellation fee. |
| GET | `admin/payments/`, `admin/subscriptions/`, `admin/dues/` | Filters: `status`, `payment_type` / `plan` / `due_type`, `captain`, dates. |
| POST | `admin/dues/{id}/waive/`, `.../settle/` | `settle` records a due paid outside the app. |
| GET | `admin/tickets/`, `admin/tickets/{id}/` | Filters: `status`, `category`. |
| POST | `admin/tickets/{id}/reply/` | `{"body"}`. Notifies the user. |
| POST | `admin/tickets/{id}/status/` | `{"status", "note"?}`. |
| GET | `admin/sos/` | Filter: `status`. |
| POST | `admin/sos/{id}/acknowledge/`, `.../resolve/` | `resolve` takes `{"reason"}` as the note. Acknowledging tells the user help is coming. |
| GET, POST | `admin/promos/` | Public promo codes. POST creates one. |
| GET, PATCH | `admin/promos/{id}/`, `admin/fares/{id}/`, `admin/plans/{id}/`, `admin/config/` | Edit promo codes, fares, plan prices, and Platform configuration. |
| GET | `admin/fares/`, `admin/plans/`, `admin/audit-log/` | |
| POST | `admin/broadcast/` | `{"audience": "CUSTOMERS"\|"CAPTAINS"\|"ALL", "title", "message"}`. Sends a notification to every active user in the audience. |

## Development-only helpers

These work only with `DJANGO_DEBUG=1`:

- `python manage.py seed_demo_data` creates demo customers and captains.
- `python manage.py simulate_payment <provider_order_id>` marks a mock payment as paid.
- `python manage.py run_periodic_jobs` reminds captains before a daily plan ends, expires plans, closes finished ride-share days, and moves timed-out offers. Run it every minute in production.
- `python manage.py setup_admin_roles` creates the Operations, Support and Finance admin groups (works in production too).

## Test sequence

1. Send an OTP and verify it for a customer and for a captain.
2. As the captain, submit KYC and vehicle details, then get approved in the admin. Choose a plan, send a location, and call `status/online/`.
3. As the customer, `POST rides/` with pickup and drop coordinates.
4. As the captain, check `offers/`, then `accept`, `arrived`, `start` (with the rider's PIN from `rides/{id}/`), and `complete`.
5. As the customer, pay with `payment/` if the ride was online, then rate the captain.
