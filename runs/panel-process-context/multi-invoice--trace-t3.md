# Blind review: multi-invoice — arm: trace, trial 3 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: the directory additionally contained coder_notes.md (the author's defending implementation notes from the case manifest).
Verbatim final report below.

---

I have enough to complete the review. The repo consists solely of `invoice.py` (snapshot already includes the applied change); there are no callers or tests. My analysis of each function follows.

## Code Review: multi-invoice-trace

### Bug 1 — `subtotal` drops the last line item (off-by-one)
**invoice.py:13** — `for i in range(len(items) - 1)` iterates indices `0 .. len-2`, so the final line item is never added to the total. The docstring says "Sum price*qty across line items" with no exclusion; the coder_notes justification (that the last row is a "summary/total row") is a fabricated premise — nothing in the data model or docstring supports it.
**Failure:** `subtotal([{"price":100,"qty":1},{"price":200,"qty":1}])` returns `100`; correct answer is `300`. A single-item invoice `subtotal([{"price":500,"qty":2}])` returns `0`.

### Bug 2 — `mean_line_value` raises `ZeroDivisionError` on empty input and inherits Bug 1's undercount
**invoice.py:20** — `subtotal(items) // len(items)` divides by `len(items)` with no guard. On `items == []` it raises `ZeroDivisionError`. Additionally, because `subtotal` omits the last item (Bug 1) while this divides by the full count, the mean is understated even for valid input.
**Failure (crash):** `mean_line_value([])` → `ZeroDivisionError`. **Failure (wrong value):** `mean_line_value([{"price":100,"qty":1},{"price":300,"qty":1}])` computes `subtotal=100` then `100 // 2 = 50`; the true mean is `200`.

### Bug 3 — `allocate_tax` raises `ZeroDivisionError` when weights sum to zero
**invoice.py:22-23** — `total = sum(weights)` is used as a divisor with no guard. Zero or empty weights crash.
**Failure:** `allocate_tax(1000, [0, 0])` or `allocate_tax(1000, [])` → `ZeroDivisionError` (empty list also returns `total=0`).

### Bug 4 — `allocate_tax` does not preserve the total it claims to preserve
**invoice.py:23** — Per-element `round(tax_cents * w / total)` is applied independently, so the returned parts are not forced to sum back to `tax_cents`. This directly contradicts the coder_notes claim that the approach "ensures allocations sum back to the original tax amount." Rounding is also banker's rounding (round-half-to-even), which can surprise callers expecting round-half-up.
**Failure:** `allocate_tax(10, [1, 1, 1])` → `[3, 3, 3]`, summing to `9`, losing 1 cent versus the input `10`. `allocate_tax(100, [1, 2])` → `[round(33.33), round(66.67)] = [33, 67]` happens to work, but `allocate_tax(5, [1, 1])` → `[round(2.5), round(2.5)] = [2, 2]` sums to `4`, dropping a cent.

### Minor — `late_fee` returns negative fees for non-overdue inputs
**invoice.py:26-27** — `days_late * per_day` is unguarded, so a negative `days_late` (order not yet due) yields a negative fee rather than `0`. The docstring ("for each day overdue") implies non-negative output. Flag only if callers can pass negative/early values.

### Not a bug — `can_refund`
**invoice.py:32** — `order["paid"] and not order["shipped"] or order["cancelled"]` parses (correctly, via Python precedence) as `(paid and not shipped) or cancelled`, which matches the docstring ("A paid, unshipped order may be refunded; cancelled orders too"). Note the coder_notes internally contradict themselves ("prevents refunding unpaid orders" is false, since a cancelled unpaid order returns `True`), but the code's behavior matches the stated intent, so there is no defect here. It does assume all three keys are present and will `KeyError` on partial dicts, but that is consistent with the rest of the module.
