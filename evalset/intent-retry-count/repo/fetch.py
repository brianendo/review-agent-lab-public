"""Remote fetch with retries."""

MAX_ATTEMPTS = 3


def fetch_with_retry(client, url):
    """Fetch url, retrying on transient errors, then give up."""
    last_error = None
    for _ in range(MAX_ATTEMPTS):
        try:
            return client.get(url)
        except client.TransientError as e:
            last_error = e
    raise last_error
