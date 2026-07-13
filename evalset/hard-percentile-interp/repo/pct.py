"""Percentiles with linear interpolation."""


def percentile(data, p):
    """The p-th percentile (0..100) of data, using linear interpolation between
    the two nearest ranks (matching numpy's default 'linear' method)."""
    s = sorted(data)
    rank = len(s) * p / 100
    lo = int(rank)
    frac = rank - lo
    if lo + 1 < len(s):
        return s[lo] + frac * (s[lo + 1] - s[lo])
    return s[-1]
