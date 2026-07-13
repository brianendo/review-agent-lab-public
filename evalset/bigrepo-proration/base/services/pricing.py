"""Charge computation."""


def compute_charge(subscription, on_date):
    """Charge for the subscription's current cycle as of `on_date`."""
    return subscription.plan.price
