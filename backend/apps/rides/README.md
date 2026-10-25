# rides

Core ride engine.

- Models: `Ride`, `RideLocation` (recorded route), `Rating`, offers, `FareConfig`
- Statuses: REQUESTED → SEARCHING → ACCEPTED → CAPTAIN_ARRIVED → STARTED → COMPLETED (+ CANCELLED). Transitions are validated in `state.py`
- `vehicle_type` (BIKE/AUTO) is chosen by the customer; fares are per vehicle type (`pricing.py`, `FareConfig` in admin). The fare is locked when the ride is created
- Matching (`matching.py`): nearest eligible online captain with the same vehicle type inside the configured radius, one offer at a time, with timeout, reject, and row locks against double-accept
- Ride start PIN, cancellation and no-show fees, ride sharing by link (`share/{token}/`), idempotent create via `Idempotency-Key`
- Customer APIs: estimate, create, list/detail, cancel, tracking, payment, fee payment, outstanding fees, share, rating
- Captain APIs (`captain_urls.py`): offers, rides, accept/reject/arrived/start/complete/cancel/surrender/collect-cash
- Live updates are polled (`tracking/`, `offers/`); there are no WebSockets yet
