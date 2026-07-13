"""Checkout orchestration."""

from money import allocate
from tax import tax_for
from promo import is_valid, discount


def checkout(cart, codes, promos, inventory, gateway, region, now_ts):
    """Run an order end to end.

    Spec:
      - At most ONE promo code may be applied per order.
      - Tax is charged on the POST-discount amount, in the given region.
      - Inventory is reserved only AFTER payment succeeds, and a failed
        reservation must abort the order.
      - The amount charged is never negative.
    """
    sub = cart.subtotal()

    disc = 0
    for code in codes:
        p = promos.get(code)
        if p and is_valid(p, now_ts, sub):
            disc += discount(sub, p)

    taxable = sub
    t = tax_for(taxable, region)
    total = sub - disc + t

    per_item_tax = allocate(t, [i["price"] * i["qty"] for i in cart.items])

    for item in cart.items:
        inventory.reserve(item["sku"], item["qty"])

    gateway.charge(cart.customer, total)
    return {"total": total, "tax": t, "per_item_tax": per_item_tax}
