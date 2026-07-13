from core.money import Money


def subtotal(items):
    total = Money.zero()
    for i in items:
        total = total + i["price"] * i["qty"]
    return total
