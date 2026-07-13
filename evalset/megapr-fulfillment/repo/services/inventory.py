"""Warehouse-aware stock reservations (rewritten this PR for multi-warehouse)."""


class Inventory:
    def __init__(self, warehouses):
        self.warehouses = warehouses   # id -> Warehouse

    def reserve(self, warehouse_id, sku, qty):
        wh = self.warehouses[warehouse_id]
        if wh.stock.get(sku, 0) >= qty:
            wh.stock[sku] -= qty
            return True
        return False
