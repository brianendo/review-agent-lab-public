"""Cart discounting. All amounts are integer cents."""

DISCOUNT_BPS = 1000   # 10%
DISCOUNT_CAP = 2000   # $20.00 maximum discount


def cart_total(line_items):
    """Sum the price of every line item (each has 'price' and 'type')."""
    return sum(int(item["price"]) for item in line_items)


def compute_discount(line_items):
    """Compute the cart's coupon discount, in integer cents."""
    base = sum(int(item["price"]) for item in line_items)
    return min(base * DISCOUNT_BPS // 10_000, DISCOUNT_CAP)
