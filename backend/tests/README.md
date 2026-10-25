# tests

pytest-django suite covering the API end to end. Run from `backend/`:

```bash
python -m pytest
```

Files cover auth and OTP, role and object permissions, fare calculation, ride lifecycle, safety and cancellation, ride-share counting, matching, captain onboarding and API, wallet, payments and webhooks, customer extras (places, promos, referrals), support and back-office, admin pages, and periodic jobs. Shared fixtures are in `conftest.py` and `helpers.py`.

Tests run on SQLite, so row-lock behaviour is only exercised for real on PostgreSQL.
