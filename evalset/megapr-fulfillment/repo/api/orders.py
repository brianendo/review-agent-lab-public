"""Order API endpoints."""
from services.fulfillment import plan_fulfillment
from services.refund import refund


def fulfill_order(order, warehouses, inventory):
    plan = plan_fulfillment(order, warehouses)
    order.status = "fulfilled"
    return plan


def refund_order(order, amount, gateway):
    return refund(order, amount, gateway)
