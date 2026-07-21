# Blind review: toctou-reserve — opus (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

## Code Review: `toctou-reserve`

### Bug 1 (critical): Time-of-check/time-of-use race allows overselling — `shop/inventory.py:10-13`

`reserve_seat` reads availability with `get_remaining` and then decrements with a separate `decrement` call. These are two distinct, non-atomic operations, so the "never oversell" guarantee promised in the docstring is broken under concurrency.

Failure scenario: an event has `remaining == 5`. Two requests each call `reserve_seat(event_id, 5)` concurrently. Both call `get_remaining` and read `5`; both evaluate `5 < 5` as False and pass the check; both call `decrement(event_id, 5)`. 10 seats are sold against an inventory of 5 — the exact oversell the function claims to prevent. The window between the read (line 10) and the write (line 13) is unguarded (no lock, no transaction, no conditional/atomic decrement). This is the defining defect of the change.

The correct pattern is a single atomic operation — e.g. a conditional decrement executed in the database (`UPDATE ... SET remaining = remaining - qty WHERE remaining >= qty`) whose affected-row count determines success — or holding a row/table lock across the check and decrement. As written, no amount of atomicity inside `decrement` alone fixes it, because the stale `remaining` value is captured before the decrement.

### Bug 2 (minor): No validation of `qty`, so non-positive quantities misbehave — `shop/inventory.py:10-13`

`qty` is used directly with no guard. If a caller passes `qty <= 0`, the check `remaining < qty` is False for any non-negative `remaining`, so the function returns `True` and calls `decrement(event_id, qty)`. A negative `qty` decrements by a negative amount, i.e. it silently *increases* inventory (phantom seats); `qty == 0` performs a no-op decrement but still reports success. Whether this is reachable depends on the caller contract, which isn't present in the snapshot, so I flag it as secondary to the race above.

### Note on snapshot completeness

The repository snapshot contains only `shop/inventory.py`; `shop/db.py` (the source of `get_remaining`/`decrement`) is not present, so I could not confirm whether `decrement` is individually atomic. That does not affect Bug 1 — the race arises from the two separate calls in `reserve_seat` itself regardless of `decrement`'s internal behavior.
