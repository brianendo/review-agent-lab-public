"""Assign order items to warehouses (new this PR)."""


def plan_fulfillment(order, warehouses):
    """Return {warehouse_id: [items]} assigning each item to a warehouse that
    has enough stock. Each item goes to the first warehouse with stock."""
    plan = {}
    for item in order.items:
        for wh in warehouses:
            if wh.stock.get(item["sku"], 0) > item["qty"]:
                plan.setdefault(wh.id, []).append(item)
                break
    return plan
