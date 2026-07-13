"""Request rate limiting."""


class RateLimiter:
    def __init__(self, limit, window_secs):
        self.limit = limit
        self.window_secs = window_secs
        self.count = 0
        self.window_start = 0

    def allow(self, now):
        """Return True if a request at time `now` (seconds) is allowed."""
        if now - self.window_start >= self.window_secs:
            self.window_start = now
            self.count = 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False
