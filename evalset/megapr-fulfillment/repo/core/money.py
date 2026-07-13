"""Money (integer cents) and proportional allocation."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    cents: int

    def __add__(self, other):
        return Money(self.cents + other.cents)

    def __sub__(self, other):
        return Money(self.cents - other.cents)

    def __mul__(self, k):
        return Money(self.cents * k)

    @classmethod
    def zero(cls):
        return cls(0)

    def __str__(self):
        return f"${self.cents / 100:.2f}"


def allocate(total, weights):
    """Split `total` (Money) across positive int weights. Parts MUST sum to total."""
    s = sum(weights)
    return [Money(round(total.cents * w / s)) for w in weights]
