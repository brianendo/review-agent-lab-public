"""Charge computation."""
from core.money import Money
from services.proration import proration_credit


def compute_charge(subscription, on_date, account=None):
    """Net charge for the subscription's current cycle as of `on_date`.

    When `account` is given, any proration credit the account is owed is applied
    against the charge (the credit is consumed and the charge reduced, floored at
    zero). Callers that bill a real customer MUST pass the account so credits are
    honored.
    """
    base = subscription.plan.price
    if account is None:
        return base
    credit = proration_credit(account, on_date)
    net = base.cents - credit.cents
    return Money(net if net > 0 else 0)
