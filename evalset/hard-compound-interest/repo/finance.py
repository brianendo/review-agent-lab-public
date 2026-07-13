"""Compound interest."""


def future_value(principal, annual_rate, years, periods_per_year):
    """Future value of `principal` compounded `periods_per_year` times per year
    at `annual_rate` (e.g. 0.06 for 6%) for `years` years."""
    n = years * periods_per_year
    return principal * (1 + annual_rate) ** n
