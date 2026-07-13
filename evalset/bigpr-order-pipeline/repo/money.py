"""Money helpers. Amounts are integer cents unless stated."""


def to_cents(dollars):
    """Convert a dollar amount (float) to integer cents."""
    return int(dollars * 100)


def allocate(total, weights):
    """Split `total` cents across positive integer weights, proportionally.
    The returned parts must sum back to `total`."""
    s = sum(weights)
    return [round(total * w / s) for w in weights]
