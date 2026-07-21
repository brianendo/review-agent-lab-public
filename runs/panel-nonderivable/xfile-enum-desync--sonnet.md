# Blind review: xfile-enum-desync — sonnet (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

## Code Review Report

**orders/notify.py:5-9 (MESSAGES dict) — new `REFUNDED` status is missing from the notification message map, so refunded customers receive the wrong message.**

`orders/status.py` adds `REFUNDED = "refunded"` as a new first-class status (status.py:6). `orders/checkout.py`'s new `process_refund()` sets `order.state = status.REFUNDED` and then calls `notify_customer(order)` (checkout.py:6-8). But `notify.py`'s `MESSAGES` dict (notify.py:5-9) was not updated to include an entry for `status.REFUNDED`, and the fallback default in `notify_customer` (notify.py:14) is itself a specific status message: `"Your order was delivered."`

Failure scenario: an order with `order.state = "pending"` goes through `process_refund(order)`. `order.state` becomes `"refunded"`. `notify_customer` does `MESSAGES.get("refunded", "Your order was delivered.")`, which misses the dict and falls through to the default — so the customer is told **"Your order was delivered."** immediately after being refunded, which is factually wrong and likely to cause confusion/support tickets. This is the classic "cross-file enum desync": a new enum value was added in one file (status.py) without updating the corresponding lookup table in a dependent file (notify.py) that switches on that enum.

**orders/notify.py:15 (`send`) — `send` is called but never defined or imported anywhere in the repo; this diff is the first thing that makes `notify_customer` reachable, so it will now raise `NameError` at runtime.**

`notify_customer` calls `send(order.customer, msg)` (notify.py:15), but grepping the full repo snapshot shows no definition or import of `send` in `notify.py`, `checkout.py`, `status.py`, or anywhere else in `repo/`. Before this diff, `checkout.py` was just a docstring (`"""Checkout."""`) and nothing in the snapshot called `notify_customer`, so this dead code's missing `send` was never exercised. This diff adds the first call path into `notify_customer` (via `process_refund`), so it now executes.

Failure scenario: calling `process_refund(order)` reaches `notify_customer(order)` → `send(order.customer, msg)` → `NameError: name 'send' is not defined`, crashing the refund flow before the customer is notified at all (and depending on transaction/ordering elsewhere, potentially after `order.state` has already been mutated to `REFUNDED`, leaving the order in a refunded state with no notification sent and an unhandled exception surfaced to the caller).

No other issues found (e.g., `status.REFUNDED` itself is defined consistently as a string constant matching the existing pattern, and `process_refund`'s use of `status.REFUNDED` is otherwise correct).
