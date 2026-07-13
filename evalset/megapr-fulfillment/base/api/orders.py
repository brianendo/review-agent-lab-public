"""Order API endpoints."""


def cancel_order(order):
    order.status = "cancelled"
    return order
