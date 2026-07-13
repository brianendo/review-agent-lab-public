from dataclasses import dataclass, field


@dataclass
class Warehouse:
    id: str
    region: str
    stock: dict = field(default_factory=dict)   # sku -> qty on hand
