"""Result ranking."""


def rank(items):
    """Order items best-first. Each item has an int 'score' and an int 'id'."""
    return sorted(items, key=lambda it: -it["score"])
