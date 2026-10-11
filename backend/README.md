# backend

Django 5 / Django REST Framework modular monolith.

- Python 3.12+, PostgreSQL, Redis, Channels (WebSockets), Celery, JWT
- API base: `/api/v1/`
- Django Admin doubles as the MVP admin dashboard

Layout: `config/` (settings, urls, asgi), `apps/` (domain modules), `tests/`.

Rules: business logic in service layer, never trust client input (fare, status, subscription), no hard-coded business values (₹30, 1-in-5 qualifying-ride count, 3 km radius, fares).
