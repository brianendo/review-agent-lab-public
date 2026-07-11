"""Time-window membership. Timestamps are integer epoch seconds."""


def in_window(ts, start, end):
    """Return True if ts falls inside the window."""
    return start <= ts <= end
