"""Unit conversions."""


def c_to_f(celsius):
    """Convert Celsius to Fahrenheit."""
    return celsius * 9 / 5 + 32


def f_to_c(fahrenheit):
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5 / 9


def km_to_mi(km):
    """Convert kilometers to miles."""
    return km * 0.621371
