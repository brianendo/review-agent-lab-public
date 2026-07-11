"""Order totals. Amounts are integer cents."""

TAX_BPS = 800  # 8%


def subtotal(items):
    """Sum price*qty across line items."""
    return sum(i["price"] * i["qty"] for i in items)


def order_total(items, coupon_bps):
    """Total after coupon and tax, in integer cents."""
    base = subtotal(items)
    taxed = base + base * TAX_BPS // 10_000
    return taxed - taxed * coupon_bps // 10_000
