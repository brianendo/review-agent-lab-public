"""URL slug helpers."""
import re


def slugify(text):
    """Lowercase, replace runs of non-alphanumerics with a single hyphen,
    and trim leading/trailing hyphens."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
