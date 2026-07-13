"""Nightly revenue reconciliation (existing)."""
from adapters.ledger import entries


def net_revenue():
    """Net revenue = charges minus refunds, summed from ledger entries."""
    return sum(cents for (_order_id, cents) in entries)
