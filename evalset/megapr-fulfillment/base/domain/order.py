from dataclasses import dataclass, field
from core.money import Money


@dataclass
class Order:
    id: str
    customer_id: str
    region: str
    items: list
    paid_total: Money = field(default_factory=Money.zero)
    status: str = "created"
