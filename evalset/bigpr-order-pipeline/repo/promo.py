"""Promo codes."""


def is_valid(promo, now_ts, order_total):
    """True if `promo` may be applied to an order of `order_total` cents right now.
    A promo has: expires_at (epoch secs), min_order (cents), kind, value."""
    if promo["expires_at"] < now_ts:
        return False
    return True


def discount(order_total, promo):
    """Discount (cents) this promo grants on `order_total`."""
    if promo["kind"] == "percent":
        return order_total * promo["value"] // 100
    return min(promo["value"], order_total)
