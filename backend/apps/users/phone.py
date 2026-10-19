import re

PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_phone(raw):
    """Strip spaces and punctuation, then require E.164 form (e.g. +919812345678)."""
    phone = re.sub(r"[\s\-()]", "", raw or "")
    if not PHONE_RE.match(phone):
        raise ValueError("Enter the phone number in international format, e.g. +919812345678.")
    return phone
