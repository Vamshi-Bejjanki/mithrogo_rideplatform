# MithrGo Ride Platform

Single-city ride-hailing platform (Bike and Auto first). Customers book rides and pay captains in cash or online. Captains pay the platform through one of two plans:

- **Daily plan**: a 12-hour session bought per vehicle (Bike ₹30, Auto ₹50). Nothing renews automatically, and no ride fares are shared.
- **Ride-share plan**: no daily fee. Only one ride's fare per day goes to the platform, taken from the captain's first 5 rides. Every other ride that day is the captain's.

Amounts, fares and limits live in the database (admin), not in code.

Design spec: [docs/PROJECT_DESIGN.md](docs/PROJECT_DESIGN.md). Documentation index: [docs/README.md](docs/README.md).

## Status

| Folder | Purpose | State |
|---|---|---|
| `backend/` | Django 5.2 + DRF modular monolith, REST API under `/api/v1/`, Django Admin | Working MVP: auth (OTP + JWT), rides, matching, plans, wallet, payments (mock gateway), notifications, support/SOS, promos |
| `customer_app/` | Flutter app for customers | Working: auth, booking, ride tracking by polling, payment, history, support, safety |
| `captain_app/` | Flutter app for captains | Not started |
| `admin_web/` | Next.js operations console, uses the backend `admin/` API | Working |
| `website/` | Static marketing site, privacy and terms drafts | Drafts |
| `docker/` | Container config | Placeholder |
| `docs/` | Design, architecture and API docs | See [docs/README.md](docs/README.md) |

Not in the MVP yet: WebSockets and Redis live location (apps poll), Celery (a management command runs the periodic jobs), a real payment gateway and a real map SDK.

## Quick start

```bash
cd backend
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

The backend needs `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=1` and `PAYMENT_WEBHOOK_SECRET` set (see `backend/README.md`). Then run `customer_app` (`flutter run`) or `admin_web` (`npm run dev`). Details are in each folder's README.
