# notifications

`Notification` (in-app inbox) and `DeviceToken` (push registration).

- Customer: ride accepted / arriving / arrived / started / completed / cancelled, payment events
- Captain: new ride offer, ride cancelled, plan expiring/expired, KYC decisions, payment events
- Admin announcements (broadcast) reach users in bulk
- APIs: `notifications/`, `{id}/read/`, `read-all/`, `devices/` (register or remove a push token)
- Push goes through `settings.PUSH_PROVIDER` (`push.py`). The default only logs; an FCM provider needs service-account credentials
- Delivery is synchronous for now; there is no Celery
