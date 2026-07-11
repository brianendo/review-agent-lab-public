"""Bid-side order book."""


class Book:
    def __init__(self, bids):
        self.bids = sorted(bids, reverse=True)

    def best_bid(self):
        """Return the highest available bid."""
        return self.bids[0]

    def spread_to(self, ask):
        """Distance from the best bid up to an ask price."""
        return ask - self.best_bid()
