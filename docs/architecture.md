# System Design — Ride Platform

Companion to [PROJECT_DESIGN.md](PROJECT_DESIGN.md). This document describes how the system is built and how it evolves, using the same building blocks as Uber, Rapido and Namma Yatri, sized for a single-city launch.

Principle: **start as a modular monolith, split out only the parts that get hot** (location, notifications). Do not begin with microservices.

---

## 1. Requirements

### Functional
- Customer requests a ride (pickup → drop), sees fare, gets matched with a nearby captain
- Captain goes online, receives offers, accepts, navigates, starts, completes
- Live captain location visible to customer during the ride
- Pay for the ride; captain pays flat daily subscription (no commission)
- Admin approves KYC, manages users, pricing, complaints

### Non-functional
| Attribute | Target (launch city) |
|---|---|
| Match latency (request → offer shown) | < 3 s |
| Location update → customer screen | < 2 s |
| Availability | 99.5% initially, 99.9% later |
| Consistency | Strong for ride state, payments, subscriptions. Eventual is fine for location. |
| Safety | A ride is never double-accepted; a payment is never double-counted |

### Capacity estimate
| Item | Pilot | Launch city | Large city |
|---|---|---|---|
| Online captains | 50 | 2,000 | 20,000 |
| Location updates (every 4 s) | ~12/s | ~500/s | ~5,000/s |
| Ride requests / day | 200 | 10,000 | 100,000 |
| Peak ride requests / s | <1 | ~5 | ~50 |

Location writes dominate load. Ride writes are tiny by comparison. This is why location is the first thing to isolate.

---

## 2. High-Level Architecture (MVP)

```text
 Customer App (Flutter)        Captain App (Flutter)
        │  HTTPS + WSS                │  HTTPS + WSS
        └──────────────┬──────────────┘
                       ▼
              ┌──────────────────┐
              │  Load balancer / │   TLS, rate limit
              │  Nginx           │
              └───────┬──────────┘
                      ▼
        ┌──────────────────────────────┐
        │ Django (ASGI)                │
        │  REST (DRF)  +  Channels WS  │   modular monolith
        │  apps: users, captains,      │
        │  rides, subscriptions,       │
        │  payments, notifications...  │
        └───┬──────────────┬───────────┘
            │              │
     ┌──────▼─────┐  ┌─────▼───────────────┐
     │ PostgreSQL │  │ Redis                │
     │ source of  │  │ - geo index (captains)│
     │ truth      │  │ - live ride state     │
     └────────────┘  │ - Channels layer      │
                     │ - locks / rate limits │
                     │ - Celery broker       │
                     └─────┬────────────────┘
                           ▼
                    Celery workers
          (offers, timeouts, expiry, FCM, webhooks)

 External: Maps API · SMS/OTP · FCM · Payment gateway
```

Django Admin runs in the same deployment, restricted to ADMIN role and IP/VPN where possible.

---

## 3. Core Components

### 3.1 API layer
- REST under `/api/v1/`, JWT auth, role + object-level permissions
- Every state-changing endpoint calls a **service function** in the domain app. Views stay thin.
- Idempotency keys on ride creation and payment creation so mobile retries are safe

### 3.2 Location service (the hot path)
```text
Captain app ──(every 3–5 s)──► WS / POST /captains/location/
                                     │
                          validate (auth, bounds, rate)
                                     │
            ┌────────────────────────┼─────────────────────────┐
            ▼                        ▼                         ▼
   Redis GEO: GEOADD          Redis hash:               if on a ride:
   captains:online:<city>     captain:{id}:loc          publish to ride:{id}
   (for matching)             (last seen, TTL 30 s)     channel group (customer)
                                                               │
                                                      batched async write
                                                      to RideLocation (PG)
```
- **Redis holds current position**; PostgreSQL only gets sampled/batched history for rides in progress.
- TTL on the last-seen key means a captain who stops reporting drops out of matching automatically.
- Matching uses `GEOSEARCH` by radius. At larger scale, shard keys by city/cell (e.g. H3 or geohash).

### 3.3 Matching / dispatch
```text
Ride REQUESTED
   │  FareService estimate stored
   ▼
SEARCHING
   │  candidates = GEOSEARCH(pickup, radius)         ← Redis
   │  filter in one query: approved, active, ONLINE (not BUSY),
   │                       subscription ACTIVE, vehicle verified
   │  sort by distance (later: ETA, rating, acceptance rate)
   ▼
offer to captain #1  ──► push (FCM) + WS event, offer TTL (e.g. 15 s)
   │
   ├─ accept  → atomic claim (see below) → ACCEPTED
   ├─ reject  → next candidate
   └─ timeout → Celery task → next candidate
   │
   ▼ none left / max attempts → ride UNAVAILABLE (customer told, can retry)
```
Rules:
- One offer at a time per ride (sequential dispatch). It is simple and fair. Broadcast-to-N is a later optimization.
- A captain who has an outstanding offer is excluded from other offers.
- Radius, offer timeout, max attempts all come from config/DB, not code.

**Preventing double-accept:** inside one DB transaction, `SELECT ... FOR UPDATE` on the ride row, verify `status = SEARCHING` and the offer is still addressed to this captain, set `captain_id` and `status = ACCEPTED`, mark captain `BUSY`. Second attempt sees a non-SEARCHING ride and fails cleanly. A unique partial index (one active ride per captain) is the backstop.

### 3.4 Ride state machine
```text
REQUESTED → SEARCHING → ACCEPTED → CAPTAIN_ARRIVED → STARTED → COMPLETED
     │           │           │            │
     └───────────┴───────────┴────────────┴──► CANCELLED
```
- Transition table lives in one place; every endpoint goes through `ride_service.transition(ride, to, actor)`
- Checks actor ownership + allowed transition + side-effects (captain BUSY/ONLINE, timestamps, notifications)
- Every transition appended to a `RideEvent` log (who, from, to, when) for support/disputes

### 3.5 Fare service
- Inputs: distance and duration from the maps provider, plus config rows (`base_fare`, `per_km`, `minimum_fare`, `platform_customer_fee`)
- `estimated_fare` computed at request time and stored; `final_fare` computed server-side at completion from actual distance/time
- Client never sends a fare. Config is versioned so old rides keep the rates they were priced with.

### 3.6 Subscription service
- `SubscriptionPlan` (amount/duration from DB) and `CaptainSubscription`
- `is_eligible(captain)` is the single check used by go-online, matching and accept
- Celery beat expires subscriptions and sends "expiring soon" notifications
- Expiry never touches a ride already STARTED; it only blocks going online / new offers

### 3.7 Payments
```text
create order (server, amount from DB) → gateway checkout in app
        → gateway webhook (signed) → verify signature + amount → mark SUCCESS
        → activate subscription / mark ride paid
App's "success" callback only triggers a status poll. It never activates anything.
```
- Webhook handler is idempotent (unique `provider_payment_id`)
- Nightly reconciliation job compares gateway records with `Payment` rows
- Cash rides: captain confirms collection; the backend records it but never trusts the amount from the client

### 3.8 Notifications
- Event → `Notification` row + FCM push via Celery
- Time-critical (new offer) goes over both FCM and the open WebSocket; FCM wakes a backgrounded captain app

### 3.9 Admin
Django Admin for KYC, vehicles, users, subscriptions, payments, pricing, tickets. All admin write actions logged (actor, object, before/after).

---

## 4. End-to-End Flow

```text
Customer app            Backend                     Redis / Workers            Captain app
     │ POST /rides/estimate │                              │                         │
     │─────────────────────►│ maps distance + FareService  │                         │
     │◄─────────────────────│ fare                         │                         │
     │ POST /rides/         │                              │                         │
     │─────────────────────►│ create ride REQUESTED→SEARCHING                        │
     │                      │ enqueue dispatch ───────────►│ GEOSEARCH, pick #1      │
     │                      │                              │── offer (WS + FCM) ────►│
     │                      │◄──────────────── POST accept │◄────────────────────────│
     │                      │ lock row, ACCEPTED, captain BUSY                       │
     │◄── ride update (WS) ─│                              │                         │
     │         … captain streams location → Redis → WS to customer …                 │
     │                      │ arrived / start / complete (each validated)            │
     │                      │ FareService final_fare                                 │
     │ pay / cash           │ payment verify                                         │
     │ POST rating          │ captain rating updated, captain → ONLINE               │
```

---

## 5. Data Design

- **PostgreSQL** is the source of truth: users, profiles, vehicles, rides, ride events, payments, subscriptions, ratings, tickets
- UUID primary keys for public entities
- Key indexes:
  - `Ride(customer_id, created_at)`, `Ride(captain_id, created_at)`, `Ride(status)`
  - Partial unique: one non-terminal ride per captain; one non-terminal ride per customer
  - `Payment(provider_payment_id)` unique
  - `CaptainSubscription(captain_id, expires_at)`
- Constraints for statuses (check constraints / enums), `rating` 1–5, `unique(ride_id)` on Rating
- `RideLocation` is append-only and high volume: partition by month, retain a limited window (e.g. 30–90 days), then archive or drop
- Money stored as integer paise (or `Decimal`), never float

**Redis keys** (all namespaced by city for later sharding)
```text
geo:captains:{city}              GEO set of ONLINE+available captains
captain:{id}:loc                 hash, TTL 30 s
captain:{id}:offer               current offer ride id, TTL = offer timeout
ride:{id}:state                  cached status + captain id
lock:ride:{id}                   short-lived lock
rate:{user}:{endpoint}           rate limits
```

---

## 6. Real-time Design

- One WebSocket per active ride: `/ws/ride/{ride_id}/`; captains also hold a personal channel for offers
- Authenticate on connect (JWT); authorize that the user is the ride's customer or captain
- Channels layer on Redis; broadcast group per ride
- Clients must handle disconnects: on reconnect, fetch current ride state via REST, then resume stream (WS is a hint, REST is truth)
- Heartbeat/ping; server drops stale sockets
- Fallback: REST polling every few seconds if WS cannot connect

---

## 7. Reliability and Failure Handling

| Failure | Handling |
|---|---|
| Captain app loses network mid-offer | Offer TTL expires → next captain |
| Captain stops sending location | Redis TTL removes from matching; admin sees stale-captain alert |
| Worker crashes during dispatch | Dispatch task is idempotent and re-derives state from DB; periodic sweeper re-queues rides stuck in SEARCHING |
| Redis restarts | Geo index rebuilt as captains next report location (seconds); ride truth is in PostgreSQL |
| Payment webhook delayed/duplicated | Idempotent handler + reconciliation job |
| Double tap / retry from app | Idempotency keys; state-machine rejects repeated transitions |
| Maps API down | Fall back to haversine × factor for estimates; flag the ride |
| Customer cancels during offer | Transition to CANCELLED, revoke outstanding offer, free captain |

---

## 8. Security

- OTP rate-limited per phone and per IP; OTP attempts capped
- Short-lived access tokens, rotating refresh tokens, revocation list in Redis
- Object-level checks on every ride/payment/profile access
- Location payload validation (bounds, speed sanity) to reject spoofed jumps
- Secrets only from environment/secret manager; KYC documents in private object storage with signed URLs
- Admin: separate login, 2FA when possible, audit log
- PII: mask phone numbers between customer and captain where feasible (masked calling later)

---

## 9. Observability

- Structured JSON logs with `request_id`, `ride_id`, `user_id`
- Metrics: ride funnel (requested → accepted → completed), match time, offer acceptance rate, online captains, WS connections, location writes/s, payment failures, Celery queue depth
- Error tracking (Sentry or similar), uptime checks, alerts on: no captains online, match time p95 > threshold, webhook failures, queue backlog
- These feed the pilot metrics in PROJECT_DESIGN §31

---

## 10. Deployment

**Launch (single city)**
```text
1 × app server  (Django ASGI via Daphne/Uvicorn behind Nginx)   → scale to 2+ behind LB
1 × worker + beat (Celery)
Managed PostgreSQL (daily backups + PITR)
Managed Redis
Object storage (KYC docs, photos)
Docker Compose or a simple managed container platform
CI: lint + tests on PR, deploy on merge to main, DB migrations gated
Environments: local, staging, production
```

---

## 11. How This Evolves

| Stage | Trigger | Change |
|---|---|---|
| 1. Monolith | Pilot, ≤ ~500 online captains | As above |
| 2. Isolate location | Location writes slow the API | Separate location service (Go/Rust/ASGI) owning Redis geo; API calls it for matching. Namma Yatri does this with a dedicated Rust location-tracking service. |
| 3. Isolate notifications | Push volume/latency | Standalone notification worker/service |
| 4. Scale data | Millions of rides | Read replicas for history/reports, partition `Ride`, move analytics off the OLTP DB |
| 5. Event backbone | Many consumers of ride events | Kafka/Redis Streams for ride events → analytics, fraud, pricing |
| 6. Multi-city | Second city | City as a first-class key: per-city config, pricing, Redis shard, and possibly separate deployment cell |
| 7. Smarter dispatch | Enough data | ETA-based ranking via routing engine (OSRM), batching, demand/supply pricing |

### Comparison

| | Uber | Rapido | Namma Yatri | This project (MVP) |
|---|---|---|---|---|
| Business model | Commission | Captain subscription/commission by market | Flat driver subscription | Flat ₹20/day subscription |
| Architecture | Large service mesh, own geo indexing (H3), dedicated dispatch | Service-oriented, bike-first, high location volume | Open-source, Beckn protocol, Haskell core + Rust location service | Django monolith, Redis geo |
| Matching | Global batched optimization | Nearest-captain with fast offers | Nearest-driver offers | Sequential nearest-captain |
| What you take from it | Geo-cell indexing, state machines, idempotency | Bike-taxi UX, short offer windows | Subscription model, separate location service, protocol openness | Same ideas, minimal moving parts |

---

## 12. Decisions and Assumptions

1. Modular monolith first; extraction only after measuring a bottleneck
2. Redis for live state, PostgreSQL for truth
3. Sequential dispatch with server-enforced offer timeouts
4. WebSocket as push channel, REST as the source of truth for state
5. All money, fare, status and eligibility decisions are server-side
6. Cash rides supported at launch; online ride payments added after pilot
7. Beckn/ONDC compatibility deferred until after launch; keep ride and fare models cleanly separable so a protocol adapter can be added later
8. Single city, Bike only, but `city` and `vehicle_type` are columns from day one

## 13. Open Questions

- Offer timeout and max attempts: start with 15 s and 5
- Cancellation fees or captain penalties for repeated rejects
- Handling of cash-collection disputes
- Data retention period for location history (privacy policy must state it)
- Maps provider choice (Google vs Mapbox vs OSRM self-hosted) and its cost at expected volume
