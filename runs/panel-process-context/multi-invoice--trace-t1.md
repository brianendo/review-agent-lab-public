# Blind review: multi-invoice — arm: trace, trial 1 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: the directory additionally contained coder_notes.md (the author's defending implementation notes from the case manifest).
Verbatim final report below.

---

I have the full picture — the repo contains only `invoice.py`, and the diff adds all five functions. Here is my review.

---

**Review: invoice.py (multi-invoice-trace)**

**Bug 1 — `subtotal`, invoice.py:9 — off-by-one drops the last line item.**
`for i in range(len(items) - 1)` iterates indices `0 … len-2`, so the final line item is never summed. The coder's note claims the last row is a "summary/total row," but nothing in the repo establishes that convention; the docstring says "Sum price*qty across line items."
Failure: `subtotal([{"price":100,"qty":2}, {"price":50,"qty":1}])` returns `200` instead of `250`. A single-item invoice `[{"price":100,"qty":1}]` returns `0`.

**Bug 2 — `mean_line_value`, invoice.py:16 — mean is wrong because it divides an (n−1)-item sum by n, and crashes on empty input.**
It calls the buggy `subtotal` (which sums only `n-1` items) but divides by `len(items)` (all `n`), so the average is understated for every list. Additionally, an empty list makes `len(items) == 0`.
Failure: two items each worth `100` → `subtotal` returns `100` (last item dropped), `100 // 2 = 50`, but the true mean is `100`. With `items == []` it raises `ZeroDivisionError`.

**Bug 3 — `allocate_tax`, invoice.py:21 — per-weight `round()` does not preserve the total, and crashes when weights sum to zero.**
Rounding each share independently means the allocations do not sum back to `tax_cents` (the invariant the coder's note explicitly claims to guarantee), silently losing or gaining cents. It also divides by `total = sum(weights)`.
Failure: `allocate_tax(10, [1, 1, 1])` → `10/3 = 3.33 → 3` each → `[3, 3, 3]`, which sums to `9`, one cent short of `10`. `allocate_tax(100, [])` (or all-zero weights) raises `ZeroDivisionError`.

**Not a bug — `can_refund`, invoice.py:36.** Despite the missing parentheses, Python precedence (`and` binds tighter than `or`) evaluates this as `(paid and not shipped) or cancelled`, which exactly matches the stated rule "a paid, unshipped order may be refunded; cancelled orders too." No defect. (`late_fee` is likewise correct.)

Note: none of the functions guard against missing dict keys (`KeyError`), but that is a consistent shared assumption rather than a specific defect in this change.
