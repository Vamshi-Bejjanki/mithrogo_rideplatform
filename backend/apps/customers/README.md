# customers

`CustomerProfile` (photo, emergency contact, referral code) and saved places (home, work, other).

- APIs: `GET/PATCH customers/profile/`, `customers/places/` (+ `{id}/`), `customers/promos/`, `customers/referral/`, `POST customers/referral/apply/`
- Promo and referral logic is in `promotions/`; ride actions are in `rides/`
