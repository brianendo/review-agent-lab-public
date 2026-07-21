# Blind review: ext-pagination — sonnet (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

## Code Review: sync/fetch_all.py (ext-pagination)

**Bug: pagination termination relies on page size instead of the cursor, causing an infinite loop / duplicated data whenever the transaction count is an exact multiple of the page size.**

- **File:** `sync/fetch_all.py:15` (and the loop as a whole, lines 12–17)
- **Summary:** `fetch_all_transactions` decides whether to stop paging by checking `len(page["transactions"]) < 100`, rather than checking `page["next_cursor"]` (the value the function's own docstring says signals "no more pages": `next_cursor: str|None`).
- **Failure scenario:** An account has exactly 100 transactions (or 200, 300, … any exact multiple of the `limit=100` page size). The first call `get_page(account_id, None, limit=100)` returns all 100 transactions with `next_cursor: None` (API's way of saying "that's everything"). Because `len(page["transactions"]) == 100` is not `< 100`, the loop does **not** break. Instead it executes `cursor = page["next_cursor"]`, which is `None` — the same value used for the very first request. The next call `get_page(account_id, None, limit=100)` therefore re-issues the *initial* request, which returns the same first page again. This repeats forever: `fetch_all_transactions` never returns, hangs the sync job indefinitely, and (if it were ever broken out of externally) `out` would contain unbounded duplicate transactions rather than the correct set.
- **Related edge case, same root cause:** the inverse is also possible — a page can return `< 100` items while `next_cursor` is still non-`None` (e.g., a backend that paginates by time-bucket rather than strict count). In that case the current code would `break` early on `len(...) < 100` and silently truncate the result set, returning fewer than the true total number of transactions, even though more data was available via `next_cursor`.
- **Why it matters here:** this is a financial transaction sync (Plaid `/transactions`), so the two failure modes are duplicate financial records or missing financial records — both are functionally severe, and the infinite-loop variant is also an availability/resource-exhaustion problem.

**Fix direction (not applied, per instructions):** terminate the loop based on `page["next_cursor"] is None` rather than (or in addition to) the returned page length.

No other issues found in the diff — the code as written is otherwise syntactically correct and internally consistent (the `limit=100` argument and the `< 100` break threshold do agree with each other, they're just checking the wrong signal).
