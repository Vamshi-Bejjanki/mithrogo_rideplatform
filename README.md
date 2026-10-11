# Ride Platform MVP

Single-city ride-hailing platform (Bike and Auto categories first). Captains choose one of two plans: a configurable flat daily subscription (initial: ₹30/day), or a ride-share plan where only 1 ride's fare per day (from the first 5 rides) goes to the platform.

Source of truth: [docs/PROJECT_DESIGN.md](docs/PROJECT_DESIGN.md)

| Folder | Purpose |
|---|---|
| `backend/` | Django + DRF modular monolith (REST, WebSockets, Celery) |
| `customer_app/` | Flutter app for customers (Android/iOS) |
| `captain_app/` | Flutter app for captains (Android/iOS) |
| `website/` | Public marketing website |
| `admin_web/` | Custom admin dashboard (post-MVP; Django Admin first) |
| `docs/` | Architecture, API, DB, ride lifecycle, deployment docs |
| `docker/` | Dockerfiles and container config (PostgreSQL, Redis) |

Admin is Django Admin, served by the backend.
