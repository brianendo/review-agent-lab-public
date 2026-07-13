from dataclasses import dataclass
from core.money import Money


@dataclass
class Product:
    sku: str
    price: Money
    weight_g: int
