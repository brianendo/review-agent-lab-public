"""Money: integer-cent amounts."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    cents: int

    def __add__(self, other):
        return Money(self.cents + other.cents)

    def __sub__(self, other):
        return Money(self.cents - other.cents)

    @classmethod
    def zero(cls):
        return cls(0)

    def __str__(self):
        return f"${self.cents / 100:.2f}"
