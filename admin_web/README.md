# admin_web

Operations console for MithroGo (Next.js, TypeScript). It runs alongside Django Admin and uses the same backend through the `admin/` REST API, so every change is audit-logged server-side.

## Screens

- **Dashboard**: live counts (refreshes every 15 s), 7-day charts, and an SOS banner.
- **Live map**: active rides and online captains on OpenStreetMap, updated every 5 s.
- **Reports**: rides and money per day, captain earnings, CSV downloads.
- **Rides**: search and filters; ride detail with fare breakdown, status timeline, offers, recorded route, cancel and waive-fee actions.
- **Captains & KYC**: document previews, approve or reject (reason required, shown to the captain), suspend or reactivate, verify vehicles, pending dues, recent rides.
- **Customers**: activity and suspend or reactivate.
- **SOS alerts** (refreshes every 10 s), **Support tickets** with the conversation and replies, **Announcements**.
- **Payments**, **Captain plans**, **Platform dues** (mark paid or waive), **Promo codes** (create, activate or deactivate).
- **Pricing & config**: fares, plan prices, and Platform configuration. **Audit log**.

## Run

Start the backend first (see `backend/README.md`). Then:

```bash
cd admin_web
npm install
copy .env.example .env.local    # set BACKEND_URL if Django is not on 127.0.0.1:8000
npm run dev                     # http://localhost:3000
```

Sign in with an ADMIN account's phone number and password (`python manage.py createsuperuser`).

## How it talks to Django

The browser only calls this app. `next.config.mjs` rewrites `/api/v1/*` and `/media/*` to `BACKEND_URL`, so no CORS setup is needed and KYC documents load through the same origin. Tokens are kept in session storage and refreshed automatically; signing out blacklists the refresh token.

## Checks

```bash
npm run typecheck
npm run build
```

## Layout

- `app/login/`: sign-in.
- `app/(console)/`: the signed-in screens; `layout.tsx` holds the sidebar and session guard.
- `components/`: tables, badges, dialogs, charts, and the Leaflet map.
- `lib/`: API client (`api.ts`), data hooks, formatting, and response types.
