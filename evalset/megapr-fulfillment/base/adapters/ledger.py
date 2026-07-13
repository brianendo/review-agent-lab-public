"""Ledger postings. Positive = money in, negative = money out."""

entries = []


def post_charge(order, amount):
    entries.append((order.id, amount.cents))
