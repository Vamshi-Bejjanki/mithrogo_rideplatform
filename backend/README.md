# backend

Django 5.2 / Django REST Framework modular monolith for the ride platform MVP. Spec: [docs/PROJECT_DESIGN.md](../docs/PROJECT_DESIGN.md).

Admin is Django Admin, customised in `core/` (dashboard, live map, reports, announcements, audit log, KYC, dues, ticket and SOS actions). The API lives under `/api/v1/`; the admin web app (`../admin_web`) uses its `admin/` endpoints.

## Setup (development)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows; use source .venv/bin/activate elsewhere
pip install -r requirements-dev.txt
copy .env.example .env          # then edit values; never commit .env
```

Quick run with SQLite (no Postgres needed):

```bash
set DJANGO_SECRET_KEY=dev-only-change-me
set DJANGO_DEBUG=1
set PAYMENT_WEBHOOK_SECRET=dev-webhook-secret
python manage.py migrate
python manage.py createsuperuser        # asks for phone (+91...) and password; this is the admin login
python manage.py runserver
```

With PostgreSQL, set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`. The database driver is `psycopg`.

Admin: http://127.0.0.1:8000/admin/

### Admin pages and roles

- Dashboard with charts and an SOS banner, **Live map** (`/admin/live-map/`), **Reports** with CSV download (`/admin/reports/`), and **Send announcement** (`/admin/broadcast/`).
- Ride pages show the route on a map, the status timeline and the offers. Actions: cancel (with a reason), waive fee, export CSV.
- Captain pages preview KYC documents. Rejecting needs a reason, which the captain sees.
- Support tickets have a reply box and the conversation; SOS alerts can be acknowledged and resolved.
- `python manage.py setup_admin_roles` creates **Operations**, **Support** and **Finance** groups. Add a staff user to a group to limit what they see. Reports need `payments.view_payment`; announcements need `notifications.add_notification`.

## Tests

```bash
python -m pytest
```

Tests run on SQLite. The concurrency guarantees (row locks, `SELECT ... FOR UPDATE`) are only exercised for real on PostgreSQL. Run the suite against Postgres before a pilot.

## Periodic jobs

Run every minute from cron or Windows Task Scheduler (replace with Celery beat later):

```bash
python manage.py run_periodic_jobs
```

It reminds captains before a daily plan ends, expires daily plans past their end, closes finished ride-share days (applies the shortfall fee and penalty), and moves timed-out ride offers to the next captain.

## Development helpers

- `python manage.py simulate_payment <provider_order_id>`: marks a mock payment as paid, through the same signed-webhook path the real gateway uses. Refused unless `DJANGO_DEBUG` is on.

## Business rules and where they live

| Rule | Location |
|---|---|
| Plan amounts, qualifying-ride count, shortfall fee | `subscriptions.SubscriptionPlan` (admin) |
| Fares (base, per km, minimum, customer fee) | `rides.FareConfig` (admin) |
| Search radius, offer timeout, max offers, location freshness, dues limit, business timezone | `core.PlatformConfig` (admin) |
| Ride start PIN, cancellation and no-show fees and windows, referral rewards, plan reminder, share-link grace | `core.PlatformConfig` (admin). Fees and rewards default to ₹0 (off). |
| Rider and captain cancellation (fees, re-dispatch to the next captain) | `rides.services.customer_cancel`, `captain_cancel` |
| Promo codes and referrals (platform-funded; captain keeps the full fare) | `promotions.services` |
| Account deletion (anonymise, keep records) | `users.deletion` |
| SOS and ticket conversations | `support.services` |
| Eligibility to go online / accept (KYC, vehicle, plan, dues) | `captains.services.eligibility_reasons` |
| Ride state machine | `rides.state` |
| Ride-share counting (5th ride, surrender, penalty, one platform ride per day) | `subscriptions.services.record_completed_ride` and `surrender_ride` |
| Matching (nearest eligible captain, one offer at a time) | `rides.matching` |
| Payment confirmation (webhook only, idempotent, amount-checked) | `payments.services.mark_success` |

Nothing here is hard-coded in views. Changing a value in admin takes effect on the next request.

## API map (`/api/v1/`)

Full reference with request bodies, status codes, and a test sequence: [docs/api.md](../docs/api.md).


| Area | Endpoints |
|---|---|
| Health | `GET health/` |
| Auth | `POST auth/send-otp/`, `POST auth/verify-otp/`, `POST auth/refresh/`, `POST auth/logout/`, `GET auth/me/` |
| Customer | `GET/PATCH customers/profile/`, `customers/places/`, `customers/promos/`, `customers/referral/`, `POST customers/referral/apply/`, `GET/POST auth/delete-account/` |
| Captain | `GET/PATCH captains/profile/`, `GET captains/status/`, `POST captains/status/online/`, `POST captains/status/offline/`, `POST captains/kyc/`, `POST/GET captains/kyc/documents/`, `POST captains/location/`, `GET captains/earnings/` |
| Vehicles | `GET/POST captains/vehicles/` |
| Subscriptions | `GET captains/subscription/`, `GET captains/subscription/plans/`, `POST captains/subscription/create-payment/`, `POST captains/subscription/verify-payment/`, `POST captains/subscription/plan/`, `GET captains/subscription/history/`, `GET captains/subscription/dues/`, `POST captains/subscription/dues/pay/` |
| Rides (customer) | `POST rides/estimate/`, `GET/POST rides/`, `GET rides/{id}/`, `GET/POST rides/{id}/cancel/`, `GET rides/{id}/tracking/`, `POST rides/{id}/payment/`, `POST rides/{id}/fee-payment/`, `GET rides/outstanding-fees/`, `POST/DELETE rides/{id}/share/`, `POST rides/{id}/rating/`, public `GET share/{token}/` |
| Rides (captain) | `GET captains/offers/`, `GET captains/rides/`, `GET captains/rides/{id}/`, `POST captains/rides/{id}/accept|reject|arrived|start|complete|cancel|surrender|collect-cash/` |
| Payments | `POST payments/webhook/` (HMAC-signed), `GET payments/{id}/` |
| Notifications | `GET notifications/`, `POST notifications/{id}/read/`, `POST notifications/read-all/`, `POST/DELETE notifications/devices/` |
| Support | `GET/POST support/tickets/`, `GET support/tickets/{id}/`, `GET/POST support/tickets/{id}/messages/`, `GET/POST support/sos/` |
| Admin | `POST auth/admin/login/` and `admin/...` (dashboard, reports, customers, captains, vehicles, rides, payments, plans, dues, tickets, SOS, promos, fares, config, audit log, broadcast). ADMIN tokens only. |

Money is returned as strings. Errors look like `{"detail": "...", "code": "..."}`.

## Not in this MVP (deliberately)

- WebSockets and Redis live location (captains are polled via `captains/location/`; the customer polls `rides/{id}/tracking/`).
- Celery and a real payment gateway (mock payments). Push goes through `PUSH_PROVIDER` (default logs only); a Firebase (FCM) provider needs the service-account credentials.
- Final fare is the fare locked at request time. Distance-based final pricing waits for route tracking.
- Refunds. Cancellation fees, captain cancellations and promos are in; refunds wait for the real gateway.
