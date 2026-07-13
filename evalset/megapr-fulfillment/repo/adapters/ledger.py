"""Ledger postings. Positive = money in, negative = money out."""

entries = []


def post_charge(order, amount):
    entries.append((order.id, amount.cents))


def post_refund(order, amount):
    entries.append((order.id, amount.cents))
