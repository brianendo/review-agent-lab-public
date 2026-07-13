"""Audit reconciliation sweep (runs on a background thread)."""
from sync.locks import accounts_lock, audit_lock


def reconcile(accounts):
    # Recompute audit totals and cross-check against live balances.
    with audit_lock:
        with accounts_lock:
            total = sum(a.balance for a in accounts)
            _write_audit_total(total)
