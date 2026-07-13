"""Sales tax by region."""

RATES_BPS = {"CA": 725, "NY": 800, "TX": 625}


def tax_for(amount, region):
    """Tax on `amount` cents for `region`, in cents."""
    rate = RATES_BPS.get(region, 0)
    return amount * rate // 10_000
