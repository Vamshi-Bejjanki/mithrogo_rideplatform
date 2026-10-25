# captain_app

Flutter app (Android/iOS) for captains. **Not started**: this folder only holds this file. The backend side is ready (`captains/*` endpoints, see [docs/api.md](../docs/api.md)), and `../customer_app` shows the structure to follow (go_router, Riverpod, Dio with JWT refresh).

Planned flow: Splash → Login → OTP → KYC documents → Vehicle → Vehicle of the day → Plan (daily or ride-share) or wallet top-up → Home (online/offline) → Ride offer → Accept → Arrived → Start (PIN) → Complete → Earnings.
Extra: profile, documents, dues, ride history, support and SOS, settings.

Offers are polled from `captains/offers/` and location is sent to `captains/location/`; WebSockets are not available yet.
