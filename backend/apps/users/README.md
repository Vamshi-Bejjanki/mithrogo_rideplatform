# users

Custom `User` model (UUID PK, phone, optional email, role, is_active, is_verified).

- Roles: `CUSTOMER`, `CAPTAIN`, `ADMIN`
- Phone/OTP authentication abstraction (pluggable SMS provider)
- JWT issue / refresh / logout
- Role-based permissions
- APIs: `/auth/send-otp/`, `/auth/verify-otp/`, `/auth/refresh/`, `/auth/logout/`, `/auth/me/`
