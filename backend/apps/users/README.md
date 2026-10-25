# users

Custom `User` model (UUID PK, phone, optional email, role, `is_active`, `is_verified`, `deleted_at`).

- Roles: `CUSTOMER`, `CAPTAIN`, `ADMIN`. A phone number belongs to one role
- OTP login (`otp.py`) with a pluggable SMS provider (`sms.py`: console in debug, MSG91 otherwise)
- JWT issue, refresh and logout (blacklist), `tokens.py`
- Account deletion anonymises the user and keeps records (`deletion.py`)
- APIs: `auth/send-otp/`, `verify-otp/`, `refresh/`, `logout/`, `me/`, `delete-account/`, `admin/login/` (phone + password, ADMIN only)
