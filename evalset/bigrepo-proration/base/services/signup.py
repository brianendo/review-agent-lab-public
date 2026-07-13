"""New-subscription signup billing."""
from services.pricing import compute_charge
from services.tax import tax_for
from adapters.ledger import post_charge


def process_signup(subscription, account, on_date):
    charge = compute_charge(subscription, on_date)
    total = charge + tax_for(charge, account.region)
    post_charge(account, total)
    return total
