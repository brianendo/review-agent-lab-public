from core.money import Money


def apply_discount(sub, pct):
    """Return `sub` reduced by `pct` percent."""
    return sub - Money(sub.cents * pct // 100)
