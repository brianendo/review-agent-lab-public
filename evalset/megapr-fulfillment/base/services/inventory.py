"""Stock reservations."""


class Inventory:
    def __init__(self, stock):
        self.stock = dict(stock)

    def reserve(self, sku, qty):
        if self.stock.get(sku, 0) >= qty:
            self.stock[sku] -= qty
            return True
        return False
