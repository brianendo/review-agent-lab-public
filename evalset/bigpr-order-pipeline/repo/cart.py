"""Shopping cart with a cached subtotal."""


class Cart:
    def __init__(self, customer):
        self.customer = customer
        self.items = []
        self._subtotal = None

    def add_item(self, sku, price, qty):
        self.items.append({"sku": sku, "price": price, "qty": qty})
        self._subtotal = None

    def remove_item(self, sku):
        self.items = [i for i in self.items if i["sku"] != sku]

    def subtotal(self):
        if self._subtotal is None:
            self._subtotal = sum(i["price"] * i["qty"] for i in self.items)
        return self._subtotal
