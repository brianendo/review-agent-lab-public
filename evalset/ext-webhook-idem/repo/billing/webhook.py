"""Stripe payment webhook handler."""
from billing.ledger import record_payment
from billing.store import get_order


def handle_payment_succeeded(event):
    """Handle a `payment_intent.succeeded` webhook from Stripe.

    `event` is the parsed JSON body: {"id", "type", "data": {"order_id", "amount"}}.
    Marks the order paid and records the payment in our ledger.
    """
    data = event["data"]
    order = get_order(data["order_id"])
    order.status = "paid"
    record_payment(order.id, data["amount"])
    return {"received": True}
