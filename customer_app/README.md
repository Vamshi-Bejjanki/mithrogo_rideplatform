# customer_app

Flutter app (Android/iOS) for customers.

Flow: Splash → Login → OTP → Home (pickup, drop, fare, request) → Searching → Captain found/arriving → Ride started → Completed → Payment → Rating.
Extra: profile, ride history, notifications, support, emergency, settings.

Initial scope: auth, API client, secure token storage, mock locations, estimate + request + ride status. GPS/WebSockets later.
Do not duplicate backend business logic.

## Current state

- Auth: splash (restores session, retries when offline), login (phone), OTP (six-box entry, auto-submit, 30 s resend cooldown), profile setup after first sign-in.
- Home: full-screen map, "Where to?" discovery sheet, then booking sheet with Bike/Auto fares, cash or UPI/card, and Book. A banner resumes a ride still in progress; the bell shows unread notifications.
- Plan: pickup/drop search with mock places and "use current location".
- Ride: searching (radar pulse), captain on the way / arrived / on trip (captain card, plate, help and cancel, SOS), completed (fare receipt, online payment, rating), cancelled. Tracking keeps polling through brief network drops.
- Payment: online rides call `rides/{id}/payment/`, then `payments/{id}/` to check status. In dev, confirm with `python manage.py simulate_payment <order id>`.
- Tabs: Home, Your rides (history cards with status), Account (profile header and menu).
- Notifications (`notifications/`), Help and support tickets (`support/tickets/`), Safety centre (call 112 or the emergency contact, alert the safety team with a SAFETY ticket).
- Settings: account, environment (dev only), log out.
- The map is a drawn stylised map (no map SDK or API key). Replace `MapCanvas` with a real map when the key is ready.

## Running

Start the backend first (`python manage.py runserver` in `backend/`, with `DJANGO_DEBUG=1`).

```bash
flutter pub get
flutter run
```

The default API URL is `http://10.0.2.2:8000/api/v1/` (Android emulator). For iOS simulator or other hosts:

```bash
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1/
```

## Layout

- `lib/app/`: app root, router (go_router with auth redirect), config, theme, providers.
- `lib/core/`: no UI. Network (Dio + JWT refresh), secure storage, location, utils.
- `lib/shared/widgets/`: buttons, cards, loading and error views.
- `lib/features/<name>/`: `data/` (repositories), `models/`, `application/` (state), `presentation/` (screens).
