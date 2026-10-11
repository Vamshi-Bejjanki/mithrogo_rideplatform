# captains

`CaptainProfile`: KYC data, license, rating, total rides, online status, last known location.

- KYC statuses: PENDING, UNDER_REVIEW, APPROVED, REJECTED, SUSPENDED
- Online statuses: OFFLINE, ONLINE, BUSY
- APIs: profile, KYC, online/offline, earnings, location update
- Go-online rule: account active + KYC approved + verified vehicle + ACTIVE subscription
- Admin: KYC approve/reject, suspend/reactivate (audit logged)
