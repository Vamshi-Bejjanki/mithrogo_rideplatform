# backend

Django 5.2 / Django REST Framework modular monolith for the ride platform MVP. Spec: [docs/PROJECT_DESIGN.md](../docs/PROJECT_DESIGN.md).

Admin is Django Admin, customised in `core/` (dashboard, audit log, KYC and dues actions). The API lives under `/api/v1/`.

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
set OTP_RETURN_CODE_FOR_DEV=1
set PAYMENT_WEBHOOK_SECRET=dev-webhook-secret
python manage.py migrate
python manage.py createsuperuser        # asks for phone (+91...) and password; this is the admin login
python manage.py runserver
```

With PostgreSQL, set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`. The database driver is `psycopg`.

Admin: http://127.0.0.1:8000/admin/

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

It expires daily plans past their end, closes finished ride-share days (applies the shortfall fee and penalty), and moves timed-out ride offers to the next captain.

## Development helpers

- `python manage.py simulate_payment <provider_order_id>`: marks a mock payment as paid, through the same signed-webhook path the real gateway uses. Refused unless `DJANGO_DEBUG` is on.

## Business rules and where they live

| Rule | Location |
|---|---|
| Plan amounts, qualifying-ride count, shortfall fee | `subscriptions.SubscriptionPlan` (admin) |
| Fares (base, per km, minimum, customer fee) | `rides.FareConfig` (admin) |
| Search radius, offer timeout, max offers, location freshness, dues limit, business timezone | `core.PlatformConfig` (admin) |
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
| Customer | `GET/PATCH customers/profile/` |
| Captain | `GET/PATCH captains/profile/`, `GET captains/status/`, `POST captains/status/online/`, `POST captains/status/offline/`, `POST captains/kyc/`, `POST/GET captains/kyc/documents/`, `POST captains/location/`, `GET captains/earnings/` |
| Vehicles | `GET/POST captains/vehicles/` |
| Subscriptions | `GET captains/subscription/`, `GET captains/subscription/plans/`, `POST captains/subscription/create-payment/`, `POST captains/subscription/verify-payment/`, `POST captains/subscription/plan/`, `GET captains/subscription/history/`, `GET captains/subscription/dues/`, `POST captains/subscription/dues/pay/` |
| Rides (customer) | `POST rides/estimate/`, `GET/POST rides/`, `GET rides/{id}/`, `POST rides/{id}/cancel/`, `GET rides/{id}/tracking/`, `POST rides/{id}/payment/`, `POST rides/{id}/rating/` |
| Rides (captain) | `GET captains/offers/`, `GET captains/rides/`, `GET captains/rides/{id}/`, `POST captains/rides/{id}/accept|reject|arrived|start|complete|surrender|collect-cash/` |
| Payments | `POST payments/webhook/` (HMAC-signed), `GET payments/{id}/` |
| Notifications | `GET notifications/`, `POST notifications/{id}/read/` |
| Support | `GET/POST support/tickets/` |

Money is returned as strings. Errors look like `{"detail": "...", "code": "..."}`.

## Not in this MVP (deliberately)

- WebSockets and Redis live location (captains are polled via `captains/location/`; the customer polls `rides/{id}/tracking/`).
- Celery, FCM push (notifications are stored in-app only), and a real SMS or payment gateway (console SMS, mock payments).
- Final fare is the fare locked at request time. Distance-based final pricing waits for route tracking.
- Captain-initiated cancellation and cancellation fees (open questions in the design doc).
