"""Promo code lookup and validation."""


def lookup(code, all_promos):
    """Return the promo dict for `code`, or None if unknown."""
    return all_promos.get(code)


def is_expired(promo, now_ts):
    """True if the promo has expired as of `now_ts` (epoch seconds)."""
    return promo["expires_at"] < now_ts
