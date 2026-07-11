"""Memoized scaled distance."""

_cache = {}


def scaled_distance(point, scale):
    """L1 norm of point (a tuple of ints) times scale, memoized by point."""
    if point not in _cache:
        _cache[point] = sum(abs(c) for c in point) * scale
    return _cache[point]
