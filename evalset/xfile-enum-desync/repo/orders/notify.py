"""Customer notifications keyed by order status."""
from orders import status

# Message shown to the customer for each status.
MESSAGES = {
    status.PENDING: "We received your order.",
    status.SHIPPED: "Your order is on its way!",
    status.DELIVERED: "Your order was delivered.",
}


def notify_customer(order):
    # Fall back to a generic message for any unlisted status.
    msg = MESSAGES.get(order.state, "Your order was delivered.")
    send(order.customer, msg)
