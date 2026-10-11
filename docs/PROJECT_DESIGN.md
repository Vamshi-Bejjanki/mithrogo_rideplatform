# Ride Platform MVP — Product & Technical Design

## 1. Project Overview

Build a single-city ride-hailing platform for Android and iOS with two mobile applications:

1. Customer App
2. Captain App

and one web-based:

3. Admin Dashboard

The platform's initial business model is:

> Captains pay a fixed platform subscription of ₹20 per day instead of paying a commission on every completed ride.

The MVP should focus on **one city and one ride category initially (Bike)**. The architecture must be extensible later to Auto, Car, additional cities, different pricing plans, and other services.

This document is the source of truth for MVP development.

---

# 2. MVP Goals

The MVP must prove that this complete real-world flow works:

```text
Customer registers
        ↓
Customer selects pickup and drop
        ↓
Fare is estimated
        ↓
Customer requests ride
        ↓
System finds nearby eligible captain
        ↓
Captain receives ride request
        ↓
Captain accepts
        ↓
Customer sees captain
        ↓
Captain reaches pickup
        ↓
Ride starts
        ↓
Ride completes
        ↓
Customer pays
        ↓
Captain receives ride earnings
        ↓
Customer rates captain
```

Captain subscription flow:

```text
Captain registers
        ↓
KYC submitted
        ↓
Admin approves captain
        ↓
Captain pays ₹20 daily platform fee
        ↓
Subscription becomes ACTIVE
        ↓
Captain can go ONLINE
        ↓
Captain can receive rides
```

---

# 3. Explicit MVP Scope

## Include

### Customer

- Phone/OTP authentication
- Profile
- Current location
- Pickup location
- Drop location
- Fare estimate
- Ride request
- Nearby captain matching
- Captain details
- Vehicle details
- Live captain location
- Ride status
- Cancel ride
- Ride history
- Payment
- Rating
- Basic support/report issue

### Captain

- Phone/OTP authentication
- Profile
- KYC/document submission
- Vehicle registration
- Admin approval
- Daily ₹20 subscription
- Subscription status
- Online/offline status
- Ride request
- Accept/reject
- Pickup navigation
- Start ride
- Complete ride
- Earnings
- Ride history
- Rating
- Basic support

### Admin

- Secure login
- Dashboard
- Customer management
- Captain management
- KYC approval/rejection
- Vehicle management
- Live rides
- Ride history
- Subscription management
- Payment records
- Pricing configuration
- Suspend/reactivate users
- Complaints/support
- Basic reports

### Platform

- REST APIs
- PostgreSQL
- Redis
- WebSockets for real-time ride/location updates
- Push notifications
- Payment gateway integration
- Maps/location integration
- Logging
- Error handling
- Automated tests

---

# 4. Explicitly Exclude From MVP

Do NOT implement initially:

- Multiple cities
- Auto and Car categories
- Scheduled rides
- Corporate accounts
- Wallet
- Referral program
- Loyalty points
- Ride pooling
- Parcel delivery
- Food delivery
- AI chatbot
- Advanced surge pricing
- Complex driver incentive system
- Microservices
- Kubernetes
- Multiple databases
- Advanced analytics platform

These can be added after the pilot proves demand.

---

# 5. Recommended Technology Stack

## Backend

- Python 3.12+
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Django Channels / WebSockets
- Celery for asynchronous/background jobs
- JWT authentication
- Pytest or Django Test Framework

## Customer and Captain Apps

Use Flutter.

- Flutter
- Dart
- Android
- iOS
- Google Maps SDK or Mapbox
- Firebase Cloud Messaging
- Secure local storage
- WebSocket client

Use separate Flutter applications:

```text
customer_app/
captain_app/
```

Share reusable packages/components where practical, but do not create an unnecessarily complex monorepo.

## Admin

Initially use:

- Django Admin for internal operations
- A custom Django admin dashboard only where Django Admin is insufficient

A separate React/Next.js admin frontend is NOT required for MVP.

## Infrastructure

Development:

- Docker Desktop
- PostgreSQL container
- Redis container

Production can initially use a managed PostgreSQL service and managed application hosting.

---

# 6. High-Level Architecture

```text
                    ┌─────────────────────┐
                    │    Customer App     │
                    │ Flutter Android/iOS │
                    └──────────┬──────────┘
                               │
                               │ HTTPS / WebSocket
                               │
                    ┌──────────▼──────────┐
                    │   Django Backend    │
                    │     REST APIs       │
                    └───────┬───────┬─────┘
                            │       │
                ┌───────────┘       └─────────────┐
                │                                 │
        ┌───────▼────────┐               ┌────────▼───────┐
        │  PostgreSQL    │               │     Redis      │
        │ Persistent DB  │               │ Cache / state  │
        └────────────────┘               │ / realtime     │
                                         └────────────────┘
                │
        ┌───────▼────────┐
        │ Background     │
        │ Workers/Celery │
        └────────────────┘

                    ┌─────────────────────┐
                    │     Captain App     │
                    │ Flutter Android/iOS │
                    └──────────┬──────────┘
                               │
                               │ HTTPS / WebSocket
                               ▼
                         Django Backend

                    ┌─────────────────────┐
                    │    Admin Dashboard   │
                    │     Django Admin     │
                    └─────────────────────┘

External services:

- Maps provider
- SMS/OTP provider
- Firebase Cloud Messaging
- Payment gateway
```

---

# 7. Repository Structure

Use one Git repository initially.

```text
ride-platform/
│
├── backend/
│   ├── config/
│   ├── apps/
│   │   ├── users/
│   │   ├── customers/
│   │   ├── captains/
│   │   ├── vehicles/
│   │   ├── rides/
│   │   ├── payments/
│   │   ├── subscriptions/
│   │   ├── notifications/
│   │   └── support/
│   │
│   ├── tests/
│   ├── manage.py
│   └── requirements.txt
│
├── customer_app/
│
├── captain_app/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── database.md
│   ├── ride-lifecycle.md
│   └── deployment.md
│
├── docker/
│
├── .env.example
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

# 8. User Roles

## Customer

Can:

- Register/login
- Request ride
- View active ride
- Cancel ride
- Pay
- Rate captain
- View history

## Captain

Can:

- Register/login
- Submit KYC
- Register vehicle
- View subscription
- Pay subscription
- Go online/offline
- Accept/reject rides
- Start/end rides
- View earnings

## Admin

Can:

- Approve/reject captains
- Manage users
- View rides
- Manage subscriptions
- View payments
- Suspend users
- Configure pricing
- Handle complaints

---

# 9. Database Design

## User

```text
User
----
id UUID PK
phone
email nullable
first_name
last_name
role
is_active
is_verified
created_at
updated_at
```

Roles:

```text
CUSTOMER
CAPTAIN
ADMIN
```

---

## CustomerProfile

```text
CustomerProfile
---------------
id
user_id FK
profile_photo nullable
emergency_contact_name nullable
emergency_contact_phone nullable
created_at
updated_at
```

---

## CaptainProfile

```text
CaptainProfile
--------------
id
user_id FK
profile_photo nullable
date_of_birth nullable
address nullable
license_number
license_expiry nullable
kyc_status
online_status
current_latitude nullable
current_longitude nullable
last_location_at nullable
rating
total_rides
created_at
updated_at
```

KYC statuses:

```text
PENDING
UNDER_REVIEW
APPROVED
REJECTED
SUSPENDED
```

Online statuses:

```text
OFFLINE
ONLINE
BUSY
```

---

## Vehicle

```text
Vehicle
-------
id
captain_id FK
vehicle_type
registration_number
make nullable
model nullable
color nullable
is_verified
created_at
updated_at
```

Initial vehicle type:

```text
BIKE
```

---

## Ride

```text
Ride
----
id UUID PK
customer_id FK
captain_id FK nullable

pickup_address
pickup_latitude
pickup_longitude

drop_address
drop_latitude
drop_longitude

estimated_distance_km
estimated_duration_minutes

estimated_fare
final_fare

status

requested_at
accepted_at nullable
arrived_at nullable
started_at nullable
completed_at nullable
cancelled_at nullable

cancellation_reason nullable

created_at
updated_at
```

Ride statuses:

```text
REQUESTED
SEARCHING
ACCEPTED
CAPTAIN_ARRIVED
STARTED
COMPLETED
CANCELLED
```

---

## RideLocation

Do not write every GPS update directly to the main Ride table.

```text
RideLocation
------------
id
ride_id FK
captain_id FK
latitude
longitude
accuracy nullable
speed nullable
heading nullable
recorded_at
```

For high-frequency production tracking, Redis should hold current live state and PostgreSQL should store only required historical data.

---

## SubscriptionPlan

```text
SubscriptionPlan
----------------
id
name
amount
duration_days
is_active
created_at
updated_at
```

Initial plan:

```text
DAILY_20
amount = 20
duration_days = 1
```

Do not hard-code ₹20 throughout the codebase.

The amount must come from configuration/database.

---

## CaptainSubscription

```text
CaptainSubscription
-------------------
id
captain_id FK
plan_id FK
start_at
expires_at
status
payment_id nullable
created_at
updated_at
```

Statuses:

```text
PENDING
ACTIVE
EXPIRED
CANCELLED
FAILED
```

---

## Payment

```text
Payment
-------
id UUID
user_id FK
payment_type
amount
currency
provider
provider_order_id nullable
provider_payment_id nullable
status
metadata JSON
created_at
updated_at
```

Payment types:

```text
RIDE_PAYMENT
CAPTAIN_SUBSCRIPTION
```

Payment statuses:

```text
CREATED
PENDING
SUCCESS
FAILED
REFUNDED
```

---

## Rating

```text
Rating
------
id
ride_id FK
customer_id FK
captain_id FK
rating
comment nullable
created_at
```

Rating should be between 1 and 5.

---

## Notification

```text
Notification
------------
id
user_id FK
type
title
message
data JSON
is_read
created_at
```

---

## SupportTicket

```text
SupportTicket
-------------
id
user_id FK
ride_id nullable
category
description
status
created_at
updated_at
```

---

# 10. API Design

Base:

```text
/api/v1/
```

## Authentication

```text
POST /auth/send-otp/
POST /auth/verify-otp/
POST /auth/refresh/
POST /auth/logout/
GET  /auth/me/
```

---

# 11. Customer APIs

```text
GET  /customers/profile/
PATCH /customers/profile/

POST /rides/estimate/
POST /rides/
GET  /rides/
GET  /rides/{id}/
POST /rides/{id}/cancel/
GET  /rides/{id}/tracking/

POST /rides/{id}/payment/
POST /rides/{id}/rating/
```

---

# 12. Captain APIs

```text
GET   /captains/profile/
PATCH /captains/profile/

POST /captains/kyc/
POST /captains/vehicles/
GET  /captains/vehicles/

GET  /captains/subscription/
POST /captains/subscription/create-payment/
POST /captains/subscription/verify-payment/

POST /captains/status/online/
POST /captains/status/offline/

GET  /captains/rides/
GET  /captains/rides/{id}/
POST /captains/rides/{id}/accept/
POST /captains/rides/{id}/reject/
POST /captains/rides/{id}/arrived/
POST /captains/rides/{id}/start/
POST /captains/rides/{id}/complete/

GET /captains/earnings/
```

---

# 13. Location APIs

```text
POST /captains/location/
GET  /rides/{id}/location/
```

For active rides, use WebSockets for real-time updates instead of polling every few seconds.

---

# 14. WebSocket Design

Example:

```text
/ws/ride/{ride_id}/
```

Captain sends:

```json
{
  "type": "location_update",
  "latitude": 18.6725,
  "longitude": 78.0940,
  "heading": 120,
  "speed": 24
}
```

Backend broadcasts:

```json
{
  "type": "captain_location",
  "latitude": 18.6725,
  "longitude": 78.0940,
  "heading": 120
}
```

Customer receives this and updates the captain marker.

---

# 15. Ride Matching

Initial algorithm should be simple.

When a ride is requested:

1. Validate customer.
2. Validate pickup/drop.
3. Calculate estimated distance.
4. Calculate estimated fare.
5. Find captains:
   - approved
   - active
   - subscription active
   - online
   - not busy
   - within configured radius
6. Sort by distance.
7. Offer ride to nearest eligible captain.
8. If captain rejects or times out, offer next captain.
9. If no captain accepts, mark request as unavailable.

Initial search radius:

```text
3 km
```

Make this configurable.

Do not hard-code the radius.

---

# 16. Ride State Machine

Allowed transitions:

```text
REQUESTED
   ↓
SEARCHING
   ↓
ACCEPTED
   ↓
CAPTAIN_ARRIVED
   ↓
STARTED
   ↓
COMPLETED
```

Cancellation can occur from allowed intermediate states.

Never allow arbitrary status changes from the client.

The backend must validate every transition.

---

# 17. Fare Calculation

Do not hard-code fare logic inside views.

Create a dedicated service:

```text
FareService
```

Example configuration:

```text
base_fare
per_km
minimum_fare
platform_customer_fee
```

Example:

```text
fare =
base_fare
+ distance_km * per_km
```

The actual commercial pricing must be configurable from Admin.

The MVP should store both:

```text
estimated_fare
final_fare
```

---

# 18. Captain ₹20 Subscription

Core rule:

> A captain with an ACTIVE subscription can accept rides.

A captain with an expired subscription:

```text
Can login
Can view account
Can renew subscription

Cannot go ONLINE
Cannot accept new rides
```

Do not automatically cancel a ride already in progress merely because a subscription expires.

---

# 19. Payment Flow

## Captain Subscription

```text
Captain
   ↓
Select ₹20 Daily Plan
   ↓
Create payment order
   ↓
Payment gateway
   ↓
Payment success
   ↓
Backend verifies payment
   ↓
Subscription ACTIVE
   ↓
expires_at = start_at + 1 day
```

Never activate subscription solely because the mobile app says payment succeeded.

The backend must verify the payment with the payment provider/webhook.

---

## Customer Ride Payment

Initially support:

- UPI/payment gateway
- Cash, if operationally appropriate

The final ride amount must be calculated/confirmed by the backend.

Never trust a fare sent from the mobile app.

---

# 20. Customer App Screens

```text
Splash
 ↓
Login
 ↓
OTP
 ↓
Home
 ├── Pickup
 ├── Drop
 ├── Fare
 └── Request Ride
        ↓
Searching
        ↓
Captain Found
        ↓
Captain Arriving
        ↓
Ride Started
        ↓
Ride Completed
        ↓
Payment
        ↓
Rating
```

Additional screens:

```text
Profile
Ride History
Ride Details
Notifications
Help/Support
Emergency
Settings
```

---

# 21. Captain App Screens

```text
Splash
 ↓
Login
 ↓
OTP
 ↓
KYC
 ↓
Vehicle
 ↓
Subscription
 ↓
Home
 ↓
OFFLINE / ONLINE
 ↓
Ride Request
 ↓
Accept
 ↓
Navigate to Pickup
 ↓
Arrived
 ↓
Start Ride
 ↓
Complete Ride
 ↓
Earnings
```

Additional screens:

```text
Profile
Documents
Subscription
Payment History
Ride History
Ratings
Support
Settings
```

---

# 22. Admin Dashboard

Dashboard metrics:

```text
Total Customers
Total Captains
Online Captains
Active Rides
Completed Rides Today
Cancelled Rides
Subscription Revenue
Ride Revenue
Pending KYC
Open Complaints
```

Captain management:

```text
List
Search
Filter
View profile
View documents
Approve
Reject
Suspend
Reactivate
```

Ride management:

```text
Live rides
Completed rides
Cancelled rides
Ride details
Customer
Captain
Fare
Timeline
```

Subscription management:

```text
Active
Expired
Failed
Revenue
Captain subscription history
```

---

# 23. Notifications

Use Firebase Cloud Messaging.

Examples:

Customer:

```text
Captain accepted your ride.
Captain is arriving.
Captain has arrived.
Ride started.
Ride completed.
Payment successful.
```

Captain:

```text
New ride request.
Ride cancelled.
Subscription expiring.
Subscription expired.
Payment successful.
```

---

# 24. Security Requirements

Never trust mobile input.

Backend must validate:

- User permissions
- Ride ownership
- Captain ownership
- Ride status
- Subscription status
- Payment status
- Fare
- Location data
- Allowed state transitions

Use:

- JWT
- HTTPS
- Secure secrets
- Environment variables
- Rate limiting
- Input validation
- Object-level permissions
- Audit logging for admin actions

Never commit:

```text
.env
API keys
payment secrets
JWT secrets
Firebase credentials
database passwords
```

---

# 25. Testing Strategy

## Backend Unit Tests

Test:

- Authentication
- Fare calculation
- Subscription expiry
- Ride transitions
- Captain eligibility
- Matching
- Payment verification
- Permissions

## API Tests

Test:

```text
Customer cannot use captain endpoints.
Captain cannot modify another captain's ride.
Customer cannot modify another customer's ride.
Expired captain cannot accept ride.
Unapproved captain cannot go online.
Completed ride cannot be started again.
Cancelled ride cannot be completed.
```

## Mobile Tests

Test:

- Login
- API errors
- Network disconnect
- GPS permission denied
- App backgrounding
- App restart
- Payment failure
- Ride cancellation

---

# 26. Development Phases

## Phase 1 — Project Foundation

- Git repository
- Django project
- PostgreSQL
- Redis
- Docker
- Environment configuration
- CI basics
- Base API structure

## Phase 2 — Authentication

- User model
- OTP abstraction
- JWT
- Roles
- Permissions
- Tests

## Phase 3 — Captain

- Captain profile
- Vehicle
- KYC
- Admin approval
- Subscription
- Online/offline

## Phase 4 — Customer

- Profile
- Location
- Ride estimate
- Ride request

## Phase 5 — Ride Engine

- Matching
- Accept/reject
- Arrived
- Start
- Complete
- Cancel
- Ride history

## Phase 6 — Temporary Web Prototype

Build a minimal browser interface to test the complete ride flow before mobile complexity.

## Phase 7 — Flutter Customer App

Build customer MVP.

## Phase 8 — Flutter Captain App

Build captain MVP.

## Phase 9 — Maps and Live Location

- GPS
- Maps
- WebSockets
- Redis
- Background location

## Phase 10 — Payments

- Captain subscription
- Customer ride payment
- Webhooks
- Reconciliation

## Phase 11 — Notifications

- FCM
- Ride notifications
- Subscription notifications

## Phase 12 — Safety and Support

- SOS
- Emergency contact
- Report issue
- Support tickets
- Account suspension

## Phase 13 — Testing

- Unit
- API
- Integration
- Device
- Network
- Payment
- Location
- Load

## Phase 14 — Android Pilot

Launch to a limited group.

## Phase 15 — iOS

Build/sign/test using macOS/Xcode.

## Phase 16 — Production Pilot

Start with one city and a small number of captains/customers.

---

# 27. Claude Code Development Rules

Claude Code must NOT attempt to build the entire application in one prompt.

For every task:

1. Inspect the existing code.
2. Explain the proposed changes.
3. Implement only the requested scope.
4. Follow existing architecture.
5. Write/update tests.
6. Run tests.
7. Fix failures.
8. Do not modify unrelated files.
9. Do not introduce new dependencies without justification.
10. Do not invent API contracts.
11. Do not hard-code secrets.
12. Do not hard-code business values that should be configurable.
13. Update documentation when architecture changes.

Never delete working code merely to make a task easier.

---

# 28. First Claude Code Prompt

Use the following prompt as the FIRST implementation prompt.

---

## MASTER INITIAL PROMPT

You are the lead software architect and senior full-stack engineer for a new ride-hailing platform.

I am a developer with Django/Python experience but I am new to mobile app development. I will use Claude Code to build this project incrementally.

Read the project specification in `docs/PROJECT_DESIGN.md` before making implementation decisions.

The product is a single-city ride-hailing MVP with:

- Customer Flutter app for Android and iOS
- Captain Flutter app for Android and iOS
- Django + Django REST Framework backend
- PostgreSQL
- Redis
- WebSockets for real-time ride/location updates
- Django Admin for initial administration
- Payment gateway abstraction
- Firebase Cloud Messaging
- Maps/location integration

The initial business model is:

- Captains pay a configurable fixed daily platform subscription.
- Initial plan: ₹20 for 1 day.
- Captains do not pay a per-ride commission in the MVP.
- A captain with an expired subscription cannot go online or accept new rides.
- The ₹20 value must be stored/configured through the subscription plan system and must NOT be hard-coded throughout the application.

IMPORTANT DEVELOPMENT RULES:

1. Do NOT build the entire application at once.
2. Do NOT implement mobile apps yet.
3. Do NOT implement payments yet.
4. Do NOT implement live GPS/WebSockets yet.
5. Do NOT introduce microservices.
6. Do NOT add unnecessary dependencies.
7. Use a modular Django monolith.
8. Use PostgreSQL.
9. Use environment variables for secrets/configuration.
10. Write automated tests for every implemented business rule.
11. Do not trust values sent by clients for fare, subscription status, permissions, or ride status.
12. Enforce all important business rules on the backend.
13. Use UUIDs for major public-facing entities such as User and Ride where appropriate.
14. Use proper database indexes and constraints.
15. Use service-layer functions/classes for business logic rather than putting complex logic in views.
16. Keep code readable and production-oriented.
17. Do not modify unrelated code.
18. Before implementing a major architectural change, explain the proposed design.
19. After implementation, run the relevant tests and report the result.
20. If something in the specification is ambiguous, make the smallest reasonable assumption and document it rather than inventing a large feature.

FIRST TASK ONLY:

Set up the backend foundation.

Create:

```text
backend/
```

with:

- Django project
- Django REST Framework
- Custom User model
- Roles:
  - CUSTOMER
  - CAPTAIN
  - ADMIN
- PostgreSQL configuration
- Environment variable configuration
- Base `/api/v1/` API structure
- Health-check endpoint
- Proper settings separation/configuration
- `.env.example`
- `.gitignore`
- requirements file
- basic test configuration

Do NOT create rides, payments, subscriptions, maps, WebSockets, or mobile applications yet.

Before coding:

1. Inspect the repository.
2. Check whether an existing project already exists.
3. If the repository is empty, create the project structure.
4. Explain the proposed backend structure briefly.
5. Implement the foundation.
6. Run migrations.
7. Run automated tests.
8. Fix any failures.
9. Give me a concise summary of files created/changed and commands I should run next.

Do not proceed to the next development phase automatically.

Stop after the backend foundation is complete.

---

# 29. Next Claude Code Prompts

After the first phase is complete, use one prompt at a time.

## Prompt 2 — Authentication

```text
Read docs/PROJECT_DESIGN.md and inspect the existing backend.

Implement authentication and authorization only.

Requirements:
- OTP authentication abstraction
- JWT authentication
- User roles
- Role-based permissions
- /api/v1/auth/me/
- Refresh token
- Logout/token invalidation strategy appropriate for the current architecture

Do not implement rides, payments, subscriptions, maps, WebSockets, or mobile apps.

Write comprehensive tests for:
- valid authentication
- invalid authentication
- role permissions
- inactive user
- customer/captain/admin endpoint access

Run all relevant tests before finishing.
Do not modify unrelated code.
Stop after authentication is complete.
```

## Prompt 3 — Captain

```text
Implement the Captain domain from docs/PROJECT_DESIGN.md.

Create:
- CaptainProfile
- Vehicle
- KYC status
- Vehicle verification
- Captain profile APIs
- Vehicle APIs

Implement backend validation and permissions.

A captain must not be allowed to go online unless:
- captain account is active
- KYC is approved
- required vehicle is verified
- active subscription exists

Do not implement ride matching or live GPS yet.

Write tests for all business rules.
Run tests.
Stop when complete.
```

## Prompt 4 — Subscription

```text
Implement the captain subscription domain.

Requirements:
- SubscriptionPlan
- CaptainSubscription
- configurable plan amount
- configurable duration
- initial plan ₹20 / 1 day
- ACTIVE/EXPIRED/etc. statuses
- subscription history
- backend validation
- subscription eligibility check

Do not integrate the real payment gateway yet.

Create a payment abstraction/mock service so the subscription lifecycle can be tested without real money.

Write tests for:
- activation
- expiry
- renewal
- expired subscription
- captain eligibility
- duplicate/invalid activation

Run tests.
Stop after completion.
```

## Prompt 5 — Customer + Ride

```text
Implement the Customer and Ride domains from docs/PROJECT_DESIGN.md.

Implement:
- CustomerProfile
- Ride
- fare estimate service
- ride request
- ride state machine
- cancellation
- ride history

Do not implement real-time GPS or WebSockets yet.

Ride status transitions must be enforced by backend business logic.

Write tests for every allowed and invalid state transition.

Do not allow:
- unauthorized ride access
- expired/unapproved captain acceptance
- invalid ride transitions
- client-controlled final fare

Run all tests.
Stop after completion.
```

## Prompt 6 — Matching

```text
Implement the initial captain matching service.

Requirements:
- Find eligible online captains
- Active subscription required
- Approved KYC required
- Verified vehicle required
- Captain must not be busy
- Initial configurable radius: 3 km
- Sort candidates by distance
- Handle captain rejection/timeout
- Prevent two captains from accepting the same ride

Use transactions/locking where required.

Write concurrency-related tests.

Do not implement WebSockets yet.
Stop after the matching engine is tested.
```

## Prompt 7 — Flutter Customer App

```text
Now start the customer Flutter application.

Read docs/PROJECT_DESIGN.md.

Create customer_app as a Flutter Android/iOS application.

Initially implement:
- project structure
- authentication screens
- API client
- secure token storage
- home screen
- pickup/drop UI using mock locations initially
- ride estimate API integration
- ride request API integration
- ride status screen

Do NOT implement background GPS or WebSockets yet.

Keep architecture clean and testable.
Do not duplicate backend business logic in Flutter.

Run Flutter tests/analyze and fix issues.
Stop after this milestone.
```

---

# 30. Definition of Done for MVP

The MVP is NOT complete merely because screens exist.

It is complete when this real test works:

```text
1. Customer logs in
2. Captain logs in
3. Captain submits KYC
4. Admin approves captain
5. Captain pays ₹20 test subscription
6. Subscription becomes ACTIVE
7. Captain goes ONLINE
8. Customer requests a ride
9. Backend finds captain
10. Captain accepts
11. Customer sees captain
12. Captain reaches pickup
13. Captain starts ride
14. Captain completes ride
15. Final fare is calculated by backend
16. Customer pays
17. Payment is verified
18. Customer rates captain
19. Ride appears in history
20. Captain earnings appear correctly
21. Subscription eventually expires
22. Captain cannot accept another ride
23. Captain renews subscription
24. Captain can go online again
```

Only after this flow is stable should the platform be treated as an MVP ready for a controlled pilot.

---

# 31. Initial Pilot Metrics

Track these from day one:

```text
Registered customers
Registered captains
Approved captains
Active subscribers
Online captains
Ride requests
Completed rides
Cancelled rides
Captain acceptance rate
Customer cancellation rate
Average rides/captain/day
Average fare
Subscription revenue
Payment failures
Customer ratings
Captain ratings
Repeat customers
Captain subscription renewals
```

The key business metric is not downloads.

It is:

> **Completed rides per active captain per day.**

If captains pay ₹20/day but don't receive enough rides, the business model will fail regardless of how good the app looks.

---

# 32. Future Extensions

Only after the MVP proves demand:

```text
Phase 2
- Auto
- Car
- More cities
- Monthly captain plans
- Better matching
- Driver incentives
- Scheduled rides
- Wallet
- Referral
- Advanced analytics

Phase 3
- Corporate rides
- Ride pooling
- Intercity
- Fleet management
- Business accounts
- Advanced fraud detection
- Demand prediction
```

The core architecture should support these without requiring a complete rewrite.
