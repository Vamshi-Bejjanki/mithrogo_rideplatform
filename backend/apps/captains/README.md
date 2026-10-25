# captains

`CaptainProfile`: KYC data, license, rating, ride counts (completed, cancelled), online status, last known location, and the vehicle chosen for the day.

- KYC statuses: PENDING, UNDER_REVIEW, APPROVED, REJECTED, SUSPENDED
- Online statuses: OFFLINE, ONLINE, BUSY
- APIs: `profile/`, `status/` (+ `online/`, `offline/`), `kyc/`, `kyc/documents/`, `vehicle-of-day/`, `location/`, `earnings/`
- Go-online rule (`services.eligibility_reasons`): account active, KYC approved, verified vehicle, vehicle of the day chosen, active plan matching it, dues under the limit
- Admin: KYC approve/reject (reason required), suspend/reactivate, all audit logged
