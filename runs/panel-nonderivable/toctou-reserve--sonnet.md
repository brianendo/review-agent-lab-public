# Blind review: toctou-reserve — sonnet (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

## Review Report

**shop/inventory.py:8-13 — Check-then-act race condition (TOCTOU) allows overselling despite the stated invariant.**

`reserve_seat` reads `remaining` via `get_remaining(event_id)` and only afterward calls `decrement(event_id, qty)` as a separate operation, with no lock, transaction, or atomic conditional update tying the two together. The docstring explicitly promises "we never oversell," but nothing in this implementation enforces that under concurrency.

Failure scenario: an event has `remaining = 1` seat. Two requests race to buy the last seat and both call `reserve_seat(event_id, 1)` concurrently (e.g., two web workers/threads handling two checkout requests at once). Thread A calls `get_remaining(event_id)` → 1, passes the `remaining < qty` check, but hasn't yet called `decrement`. Before A calls `decrement`, Thread B also calls `get_remaining(event_id)` → still 1 (A hasn't decremented yet), and B also passes the check. Both threads now call `decrement(event_id, 1)`, both return `True`, and two seats are sold against an inventory of one — an oversell, exactly the outcome the docstring says is prevented. The fix would require the check-and-decrement to be atomic (e.g., a single conditional `UPDATE ... SET remaining = remaining - qty WHERE remaining >= qty` and checking rows-affected, or a row lock/transaction spanning both operations), but as written the two DB calls are independent and interleavable.

**shop/inventory.py:6-13 — No validation that `qty` is positive, so a negative or zero `qty` bypasses the oversell guard.**

The guard is `if remaining < qty: return False`. If a caller passes a negative `qty` (e.g., due to an upstream bug, malformed request, or malicious input), then for any non-negative `remaining`, `remaining < qty` is false, so the function proceeds to call `decrement(event_id, qty)` with a negative amount. Depending on `decrement`'s implementation (a plausible one being `remaining -= qty`), this would *increase* the remaining count rather than reserve seats — e.g., `reserve_seat(event_id, -5)` on an event with `remaining = 10` passes the check (`10 < -5` is false) and calling `decrement(event_id, -5)` inflates `remaining` to 15, fabricating inventory out of nothing while the function reports success (`True`) as if 5 seats were legitimately reserved. (Note: `shop/db.py` is not present in the provided repo snapshot, so `decrement`'s exact semantics can't be confirmed directly, but `reserve_seat` itself performs no bounds/sign check on `qty` before delegating to it, so this is a gap in the reviewed code regardless of `decrement`'s internals.)

No other issues found in the diff.
