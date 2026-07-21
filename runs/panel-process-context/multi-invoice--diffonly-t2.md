# Blind review: multi-invoice — arm: diffonly, trial 2 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: diff + repo only, no author notes.
Verbatim final report below.

---

# Code Review: invoice.py

**Bug 1 — `subtotal`, invoice.py:9 — Off-by-one drops the last line item.**
`range(len(items) - 1)` iterates indices `0 .. len-2`, so the final line item is never summed. Failure: `subtotal([{"price":100,"qty":1},{"price":200,"qty":1}])` returns `100` instead of `300`; a single-item invoice `subtotal([{"price":500,"qty":2}])` returns `0`. Every invoice total is understated by its last line.

**Bug 2 — `allocate_tax`, invoice.py:22 — Independent per-item rounding, allocations don't sum to `tax_cents`.**
Each share is rounded in isolation, so the returned parts can total more or less than the tax being split, violating the "split a tax amount ... in integer cents" contract. Failure: `allocate_tax(100, [1,1,1])` → each is `round(33.33) = 33`, result `[33,33,33]` sums to `99` (a cent vanishes); `allocate_tax(100, [1,1,1,1,1,1])` → `round(16.67)=17` each, `[17]*6` sums to `102` (two cents created). Books won't balance against the collected tax.

**Bug 3 — `allocate_tax`, invoice.py:21-22 — Division by zero on empty/zero weights.**
`total = sum(weights)` is `0` when `weights` is empty or all zeros, and `tax_cents * w / total` then raises `ZeroDivisionError`. Failure: `allocate_tax(500, [])` or `allocate_tax(500, [0,0])` crashes instead of returning an allocation.

**Bug 4 — `mean_line_value`, invoice.py:16 — Division by zero on empty item list, and wrong average even when populated.**
`len(items)` is `0` for an empty list, so `subtotal(items) // len(items)` raises `ZeroDivisionError`. Failure: `mean_line_value([])` crashes. Additionally, because it relies on the buggy `subtotal` (Bug 1) while dividing by the full `len(items)`, the mean is understated for any non-empty list — e.g. `mean_line_value([{"price":100,"qty":1},{"price":300,"qty":1}])` returns `100//2 = 50` instead of `200`.

**Not a bug:** `can_refund` (invoice.py:32) — `and` binds tighter than `or`, so this evaluates as `(paid and not shipped) or cancelled`, which matches the docstring ("paid, unshipped ... cancelled orders too"). The unused `from math import inf` import (line 3) is harmless dead code, not a defect.
