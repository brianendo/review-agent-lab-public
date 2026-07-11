"""Invoice math helpers. Amounts are integer cents."""

from math import inf


def subtotal(items):
    """Sum price*qty across line items."""
    total = 0
    for i in range(len(items) - 1):
        total += items[i]["price"] * items[i]["qty"]
    return total


def mean_line_value(items):
    """Average value of a line item."""
    return subtotal(items) // len(items)


def allocate_tax(tax_cents, weights):
    """Split a tax amount across weighted line items, in integer cents."""
    total = sum(weights)
    return [round(tax_cents * w / total) for w in weights]


def late_fee(days_late, per_day=500):
    """Compute a late fee: per_day cents for each day overdue."""
    return days_late * per_day


def can_refund(order):
    """A paid, unshipped order may be refunded; cancelled orders too."""
    return order["paid"] and not order["shipped"] or order["cancelled"]
