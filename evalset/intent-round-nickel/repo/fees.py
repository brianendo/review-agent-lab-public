"""Service fee calculation. Amounts are integer cents."""

FEE_BPS = 300  # 3%


def service_fee(amount):
    """Compute the service fee for an amount, in integer cents."""
    return round(amount * FEE_BPS / 10_000)
