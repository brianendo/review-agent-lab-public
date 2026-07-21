# Blind review: toctou-reserve — haiku (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

## Review Report

**BUG FOUND**

**File:** `shop/inventory.py`, lines 10-13

**Summary:** Time-Of-Check-Time-Of-Use (TOCTOU) race condition between seat availability check and decrement operation.

**Concrete Failure Scenario:**
Initial state: 10 seats available for event_id=1

1. Thread A: `reserve_seat(1, 5)`
   - Line 10: `get_remaining(1)` returns 10
   - Line 11: Check passes (10 >= 5)
   - Yields control

2. Thread B: `reserve_seat(1, 8)`
   - Line 10: `get_remaining(1)` returns 10
   - Line 11: Check passes (10 >= 8)
   - Line 13: `decrement(1, 8)` → 2 seats remain

3. Thread A resumes:
   - Line 13: `decrement(1, 5)` → -3 seats remain

Result: System oversells by 3 seats, violating the documented contract that "we never oversell."

**Root Cause:** The check on line 11-12 and the decrement on line 13 are not atomic. Multiple concurrent calls can read the same remaining count before any of them execute their decrements, causing the aggregate reservations to exceed actual inventory.
