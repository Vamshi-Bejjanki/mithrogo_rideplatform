# admin_web

Custom admin web dashboard (React/Next.js). **Not required for MVP** — Django Admin is used first (see `docs/PROJECT_DESIGN.md` §5).

Build this only where Django Admin becomes insufficient:

- Dashboard metrics (customers, captains, online captains, active rides, revenue, pending KYC, complaints)
- Captain management and KYC document review
- Live rides map and ride timeline
- Subscription and payment reports
- Pricing configuration, complaints/support

Uses the same `/api/v1/` backend APIs with ADMIN-role JWT auth. Admin actions must be audit logged server-side.
