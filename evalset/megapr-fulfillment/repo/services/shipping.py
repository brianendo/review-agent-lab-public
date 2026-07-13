"""Shipping cost and per-shipment split (new this PR)."""
from core.money import Money, allocate
from config import FREE_SHIP_THRESHOLD, SHIP_FLAT
from services.pricing import subtotal


def shipping_cost(order):
    sub = subtotal(order.items)
    if sub.cents >= FREE_SHIP_THRESHOLD:
        return Money.zero()
    return Money(SHIP_FLAT)


def split_shipping(cost, shipments):
    """Split `cost` across shipments by item count; parts sum to cost."""
    weights = [len(items) for items in shipments]
    return allocate(cost, weights)
