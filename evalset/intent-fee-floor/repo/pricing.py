"""Order pricing helpers. All amounts are integer cents."""

PLATFORM_FEE_BPS = 250  # 2.5%


def subtotal_cents(line_items: list[dict]) -> int:
    """Sum line item prices (each an integer-cent 'price') for an order."""
    return sum(int(item["price"]) for item in line_items)


def platform_fee(subtotal: int) -> int:
    """Compute the platform fee for an order subtotal, in integer cents."""
    return subtotal * PLATFORM_FEE_BPS // 10_000
