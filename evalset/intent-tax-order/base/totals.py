"""Order totals. Amounts are integer cents."""

TAX_BPS = 800  # 8%


def subtotal(items):
    """Sum price*qty across line items."""
    return sum(i["price"] * i["qty"] for i in items)
