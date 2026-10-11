# rides

Core ride engine.

- Models: `Ride`, `RideLocation`, `Rating`
- Statuses: REQUESTED → SEARCHING → ACCEPTED → CAPTAIN_ARRIVED → STARTED → COMPLETED (+ CANCELLED)
- Services: `FareService`, matching service, ride state machine (every transition validated server-side)
- `Ride.vehicle_type` (BIKE/AUTO) chosen by the customer; fares are configured per vehicle type
- Matching: nearest eligible captain with the same vehicle type within configurable radius (default 3 km), handle reject/timeout, prevent double-accept with locking
- WebSocket consumer: `/ws/ride/{ride_id}/`
- Live location in Redis; only needed history in PostgreSQL
- APIs: estimate, create, list/detail, cancel, tracking, rating; captain accept/reject/arrived/start/complete
