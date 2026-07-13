"""Fetch every transaction from the Plaid /transactions endpoint."""
from sync.client import get_page


def fetch_all_transactions(account_id):
    """Return ALL transactions for an account by paging through the API.

    get_page(account_id, cursor) -> {"transactions": [...], "next_cursor": str|None}
    """
    out = []
    cursor = None
    while True:
        page = get_page(account_id, cursor, limit=100)
        out.extend(page["transactions"])
        if len(page["transactions"]) < 100:
            break
        cursor = page["next_cursor"]
    return out
