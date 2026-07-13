"""Proration credits."""
from core.money import Money


def proration_credit(account, on_date):
    """Credit owed to `account` to apply against its next charge."""
    return account.credit_balance
