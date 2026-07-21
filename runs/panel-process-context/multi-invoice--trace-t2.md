# Blind review: multi-invoice — arm: trace, trial 2 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: the directory additionally contained coder_notes.md (the author's defending implementation notes from the case manifest).
Verbatim final report below.

---

All three bugs confirmed empirically. Here is my review.

---

## Code Review: invoice.py

**Bug 1 — `subtotal` drops the last line item (off-by-one).** `invoice.py:9`
The loop `for i in range(len(items) - 1)` iterates indices `0 .. len-2`, so the final line item is never summed. The docstring says "Sum price*qty across line items" — nothing in the repo supports the coder's claimed "summary/total row" convention; a plain list of line items is the expected input.
Failure: `subtotal([{"price":500,"qty":2}, {"price":300,"qty":1}])` returns `1000` instead of `1300`. A single-item invoice `subtotal([{"price":800,"qty":1}])` returns `0`.

**Bug 2 — `mean_line_value` is wrong for the same reason, plus divides by the full count.** `invoice.py:16`
It divides the (already-undercounted) `subtotal` by `len(items)`, mixing a sum of `n-1` items over a denominator of `n`. Even setting aside Bug 1, the two functions use inconsistent element counts.
Failure: `mean_line_value([{"price":800,"qty":1}])` returns `0` (subtotal is `0`, `0 // 1 = 0`) instead of `800`. Also, an empty list raises `ZeroDivisionError` (`subtotal([]) // len([])`).

**Bug 3 — `allocate_tax` does not preserve the total tax amount.** `invoice.py:22`
Each share is rounded independently via `round(tax_cents * w / total)`, so the sum of the returned list is not guaranteed to equal `tax_cents` — directly contradicting the function's stated contract ("must sum back to the original tax amount"). No remainder is redistributed.
Failure: `allocate_tax(100, [1,1,1])` returns `[33, 33, 33]`, which sums to `99` — one cent of tax is lost. (Rounding can also overshoot, e.g. producing a sum greater than `tax_cents`.) Additionally, empty or all-zero `weights` makes `total == 0`, raising `ZeroDivisionError`.

**Not a bug — `can_refund`.** `invoice.py:32`
`order["paid"] and not order["shipped"] or order["cancelled"]` evaluates as `(paid and not shipped) or cancelled` due to Python precedence, which matches the documented rule ("paid, unshipped, or cancelled"). Correct as written (assuming all three keys are always present).

**Minor (not flagged as a bug):** the `from math import inf` import (line 3) is unused; `late_fee` returns a negative fee for negative `days_late`, but that is outside its documented input domain.
