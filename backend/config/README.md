# config

Django project configuration.

- Split settings (base / dev / prod), all secrets from environment variables
- Root URL conf mounting `/api/v1/`
- ASGI (Channels) and WSGI entrypoints
- Celery app and Redis/Postgres configuration
