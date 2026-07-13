"""Order pricing. All amounts are integer cents."""


def subtotal(items):
    """Sum price * qty across line items."""
    return sum(item["price"] * item["qty"] for item in items)


def discount_amount(sub, promo):
    """Return the discount (in cents) a single promo applies to subtotal `sub`."""
    if promo["kind"] == "percent":
        return sub * promo["value"] // 100
    return promo["value"]


def tax(amount, rate_bps):
    """Tax on `amount` at rate_bps basis points."""
    return amount * rate_bps // 10_000
