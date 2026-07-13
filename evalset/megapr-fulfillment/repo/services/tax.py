from core.money import Money
from config import TAX_RATES


def tax_for(amount, region):
    return Money(amount.cents * TAX_RATES.get(region, 0) // 10_000)
