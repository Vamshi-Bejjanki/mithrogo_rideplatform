# config

Django project configuration.

- `settings.py`: one settings module. Environment-specific values come from environment variables (see `../.env.example`): secret key, debug, hosts, PostgreSQL (SQLite when `POSTGRES_DB` is empty), JWT lifetimes, `SMS_PROVIDER` (console in debug, MSG91 otherwise), `PAYMENT_PROVIDER`, `PAYMENT_WEBHOOK_SECRET`, `PUSH_PROVIDER`.
- `urls.py`: mounts Django admin at `/admin/` and the API at `/api/v1/`.
- `asgi.py` / `wsgi.py`: entrypoints. Channels and Celery are not configured yet.
