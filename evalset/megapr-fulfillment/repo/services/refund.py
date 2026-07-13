"""Order refunds (new this PR)."""
from adapters.ledger import post_refund


def refund(order, amount, gateway):
    """Refund `amount` (Money) for `order`."""
    gateway.refund(order.customer_id, amount)
    order.refunded_total = order.refunded_total + amount
    post_refund(order, amount)
    return order.refunded_total
