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

A phone number belongs to one role. A captain's number can't sign in with `"role": "CUSTOMER"`, and the reverse.

## Customer

| Method | Path | Body / notes |
|---|---|---|
| GET, PATCH | `customers/profile/` | PATCH fields: `first_name`, `last_name`, `email`, `emergency_contact_name`, `emergency_contact_phone`. |

## Rides (customer)

| Method | Path | Body / notes |
|---|---|---|
| POST | `rides/estimate/` | `{"vehicle_type": "BIKE", "pickup_latitude", "pickup_longitude", "drop_latitude", "drop_longitude"}`. Returns `distance_km`, `duration_minutes`, `fare`, `currency`. Stores nothing. |
| GET | `rides/` | The 50 most recent rides. |
| POST | `rides/` | Estimate fields plus `pickup_address`, `drop_address`, `payment_method` (`ONLINE` or `CASH`, default `ONLINE`). Optional `Idempotency-Key` header. Starts matching immediately. |
| GET | `rides/{id}/` | Ride details. Also moves a stalled search forward. |
| POST | `rides/{id}/cancel/` | Allowed until the ride starts. |
| GET | `rides/{id}/tracking/` | Ride status, pickup and drop, and the captain's latest location and vehicle once a captain has accepted. |
| POST | `rides/{id}/payment/` | Creates an online payment for a completed `ONLINE` ride. Returns a payment with `provider_order_id`. |
| POST | `rides/{id}/rating/` | `{"rating": 1-5, "comment": "..."}`. Only for completed rides, once per ride. |

A customer can have only one active ride at a time. The fare is fixed when the ride is created. The client cannot change it.

## Captain profile, status, and location

| Method | Path | Body / notes |
|---|---|---|
| GET, PATCH | `captains/profile/` | PATCH fields: `date_of_birth`, `address`. Status fields are read-only. |
| GET | `captains/status/` | `eligible`, `reasons`, and a plain-language `message`. Use it to show why a captain can't go online. |
| POST | `captains/status/online/` | Fails with `403` and the reason if the captain isn't eligible. |
| POST | `captains/status/offline/` | Fails with `409` while on a ride. |
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
| POST | `captains/rides/{id}/start/` | `CAPTAIN_ARRIVED` → `STARTED`. |
| POST | `captains/rides/{id}/complete/` | `STARTED` → `COMPLETED`. Updates earnings and the ride-share count. |
| POST | `captains/rides/{id}/surrender/` | Ride-share plan only. Marks this ride as the platform ride, if it's one of the first four rides today. Once per day. |
| POST | `captains/rides/{id}/collect-cash/` | For completed `CASH` rides. Records the cash as collected. |
| GET | `captains/rides/` | Optional `?status=COMPLETED`. The 50 most recent rides. |
| GET | `captains/rides/{id}/` | Details of one of this captain's rides. |

Ride status flow: `REQUESTED` → `SEARCHING` → `ACCEPTED` → `CAPTAIN_ARRIVED` → `STARTED` → `COMPLETED`. `CANCELLED` is reachable before the ride starts. Invalid moves return `409 invalid_transition`.

## Captain plans and dues

| Method | Path | Body / notes |
|---|---|---|
| GET | `captains/subscription/` | Current plan, `eligible`, `reasons`, `pending_dues`, and today's ride-share progress. |
| GET | `captains/subscription/plans/` | Active plans with their current prices. |
| POST | `captains/subscription/create-payment/` | `{"plan_code": "DAILY_30"}`. Creates a payment. The plan activates only after the gateway confirms it. |
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
| GET, POST | `support/tickets/` | POST: `{"category": "RIDE_ISSUE"\|"PAYMENT"\|"SAFETY"\|"ACCOUNT"\|"OTHER", "description", "ride_id"?}`. `ride_id` must be a ride the user took part in. |

## Development-only helpers

These work only with `DJANGO_DEBUG=1`:

- `python manage.py seed_demo_data` creates demo customers and captains.
- `python manage.py simulate_payment <provider_order_id>` marks a mock payment as paid.
- `python manage.py run_periodic_jobs` expires plans, closes finished ride-share days, and moves timed-out offers. Run it every minute in production.

## Test sequence

1. Send an OTP and verify it for a customer and for a captain.
2. As the captain, submit KYC and vehicle details, then get approved in the admin. Choose a plan, send a location, and call `status/online/`.
3. As the customer, `POST rides/` with pickup and drop coordinates.
4. As the captain, check `offers/`, then `accept`, `arrived`, `start`, and `complete`.
5. As the customer, pay with `payment/` if the ride was online, then rate the captain.
