"""Money transfer between accounts."""
from sync.locks import accounts_lock, audit_lock


def transfer(src, dst, amount):
    with accounts_lock:
        with audit_lock:
            src.balance -= amount
            dst.balance += amount
            _append_audit(src, dst, amount)
