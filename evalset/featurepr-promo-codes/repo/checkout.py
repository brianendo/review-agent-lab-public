"""Checkout orchestration."""

from pricing import subtotal, discount_amount, tax
from promo import lookup, is_expired


def checkout(cart, codes, all_promos, inventory, gateway, now_ts):
    """Apply promo codes to a cart, compute the total, reserve inventory, and charge.

    Spec:
      - At most ONE promo code may be applied to an order.
      - Tax is charged on the post-discount amount.
      - Inventory is reserved only after the payment succeeds.
      - The amount charged is never negative.
    Returns the charged total (cents).
    """
    sub = subtotal(cart["items"])

    total_discount = 0
    for code in codes:
        promo = lookup(code, all_promos)
        if promo is None:
            continue
        if is_expired(promo, now_ts):
            continue
        total_discount += discount_amount(sub, promo)

    taxable = sub
    t = tax(taxable, cart["tax_bps"])
    total = sub - total_discount + t

    for item in cart["items"]:
        inventory.decrement(item["sku"], item["qty"])

    gateway.charge(cart["customer"], total)
    return total
