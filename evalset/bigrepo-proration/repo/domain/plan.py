from dataclasses import dataclass
from core.money import Money


@dataclass
class Plan:
    name: str
    price: Money   # charged once per billing cycle
