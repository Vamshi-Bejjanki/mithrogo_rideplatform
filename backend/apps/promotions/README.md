# promotions

Promo codes and referrals. Both are platform-funded: the captain always keeps the full fare.

- Models: `PromoCode` (discount type and value, limits, validity), `PromoRedemption`
- Customer APIs: `customers/promos/`, `customers/referral/`, `customers/referral/apply/`
- Referral rewards default to ₹0 (off) and are set in `core.PlatformConfig`
- Staff manage promos in Django Admin or `admin_web` (`admin/promos/`)
