from dataclasses import dataclass, field
from core.money import Money


@dataclass
class Account:
    id: str
    region: str
    # Proration credits owed back to the customer (e.g. from a mid-cycle
    # downgrade). These must be applied against the next charge.
    credit_balance: Money = field(default_factory=Money.zero)
