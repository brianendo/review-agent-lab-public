"""Ledger postings."""

_entries = []


def post_charge(account, amount):
    _entries.append((account.id, amount.cents))
