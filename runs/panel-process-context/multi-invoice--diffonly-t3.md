# Blind review: multi-invoice — arm: diffonly, trial 3 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: diff + repo only, no author notes.
Verbatim final report below.

---

My analysis is confirmed. Here is the review.

---

**Review: `invoice.py` (new invoice math helpers)**

**BUG 1 — `subtotal`, line 9: off-by-one loop drops the last line item.**
`for i in range(len(items) - 1)` iterates indices `0 … len-2`, so the final line item is never summed.
Failure: `subtotal([{ "price":100, "qty":1 }, { "price":200, "qty":1 }])` returns `100` instead of `300`. Every invoice with N items undercounts by the value of its last item; a single-item invoice returns `0`.

**BUG 2 — `mean_line_value`, line 16: propagates the `subtotal` undercount and divides by the full count.**
It computes `subtotal(items) // len(items)`, but `subtotal` omits the last item while `len(items)` counts all of them, so the average is understated.
Failure: `mean_line_value([{ "price":100, "qty":1 }, { "price":200, "qty":1 }])` returns `100 // 2 = 50`; the true mean is `150`. (Separately, an empty `items` list raises `ZeroDivisionError` here.)

**BUG 3 — `allocate_tax`, line 22: independently-rounded shares don't sum back to `tax_cents`, losing/gaining cents.**
Each share is `round(tax_cents * w / total)` computed in isolation with no remainder reconciliation, so the allocation total drifts from the input.
Failure: `allocate_tax(10, [1,1,1])` returns `[3, 3, 3]`, which sums to `9` — one cent of tax vanishes. With other weights it can also over-allocate (e.g. banker's rounding of `.5` cases). For a function whose job is to *split* an amount, the parts must equal the whole. (Also: `weights` summing to `0`, e.g. `[0,0]`, raises `ZeroDivisionError`.)

**MINOR — `late_fee`, line 27: no floor at zero for non-overdue inputs.**
`days_late * per_day` returns a negative fee for negative `days_late`.
Failure: `late_fee(-3)` returns `-1500`. If a caller passes a not-yet-due delta, this yields a negative (credit) fee rather than `0`. Depends on intended contract, but worth confirming.

**Not a bug — `can_refund`, line 32.** `order["paid"] and not order["shipped"] or order["cancelled"]` parses as `(paid and not shipped) or cancelled`, which matches the docstring ("a paid, unshipped order… cancelled orders too"). Correct as written.

**Note:** `from math import inf` (line 3) is unused — dead import, not a defect.
