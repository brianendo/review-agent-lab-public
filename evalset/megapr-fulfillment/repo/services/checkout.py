"""Checkout (existing)."""
from services.pricing import subtotal
from services.tax import tax_for


def checkout(order, inventory, gateway):
    sub = subtotal(order.items)
    for i in order.items:
        inventory.reserve(i["sku"], i["qty"])
    total = sub + tax_for(sub, order.region)
    gateway.charge(order.customer_id, total)
    order.paid_total = total
    order.status = "paid"
    return total
