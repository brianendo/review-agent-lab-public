"""Sales tax."""
from core.money import Money

RATES = {"CA": 725, "NY": 800, "TX": 625}


def tax_for(amount, region):
    return Money(amount.cents * RATES.get(region, 0) // 10_000)
