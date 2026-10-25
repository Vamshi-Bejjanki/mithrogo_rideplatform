# support

- `SupportTicket` (user, optional ride, category, status) and `TicketMessage` (conversation between the user and staff)
- `SosAlert`: emergencies from the apps. Every admin is notified and a SAFETY ticket is opened
- APIs: `support/tickets/`, `tickets/{id}/`, `tickets/{id}/messages/`, `support/sos/`
- Staff handle tickets and SOS from Django Admin or `admin_web`
