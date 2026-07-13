from dataclasses import dataclass
from datetime import date
from domain.plan import Plan


@dataclass
class Subscription:
    account_id: str
    plan: Plan
    cycle_start: date
