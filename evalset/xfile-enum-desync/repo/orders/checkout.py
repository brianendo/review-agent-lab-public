"""Checkout marks an order refunded on a successful refund."""
from orders import status
from orders.notify import notify_customer


def process_refund(order):
    order.state = status.REFUNDED
    notify_customer(order)
