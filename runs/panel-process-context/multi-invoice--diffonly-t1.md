# Blind review: multi-invoice — arm: diffonly, trial 1 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: diff + repo only, no author notes.
Verbatim final report below.

---

## Code Review: multi-invoice-diffonly

### Bug 1 — `subtotal` drops the last line item (off-by-one)
**invoice.py:9** — `for i in range(len(items) - 1)` iterates indices `0 .. len-2`, so the final line item is never summed.
**Failure scenario:** `subtotal([{"price": 100, "qty": 1}, {"price": 200, "qty": 1}])` returns `100` instead of `300`. Any single-item invoice returns `0`. This corrupts every downstream total.

### Bug 2 — `mean_line_value` computes a wrong average and divides by zero on empty input
**invoice.py:16** — It divides the (already-undercounted) `subtotal(items)` by `len(items)`. The numerator omits the last item but the denominator counts all items, so the mean is systematically low; and an empty list raises `ZeroDivisionError`.
**Failure scenario:** For two items worth 100 and 200, `subtotal` returns 100, so `mean_line_value` returns `100 // 2 = 50` instead of `150`. `mean_line_value([])` raises `ZeroDivisionError`.

### Bug 3 — `allocate_tax` allocations do not sum back to `tax_cents` (rounding drift)
**invoice.py:22** — Each share is `round(tax_cents * w / total)` computed independently, so the rounded parts need not add up to `tax_cents`. For an integer-cents money split this loses/gains cents.
**Failure scenario:** `allocate_tax(10, [1, 1, 1])` → `[round(3.33), round(3.33), round(3.33)]` = `[3, 3, 3]`, which sums to `9`, losing one cent of tax. (Also, empty `weights` / weights summing to `0` raises `ZeroDivisionError`.)

### Minor — `late_fee` returns a negative fee for non-overdue orders
**invoice.py:27** — `days_late * per_day` with a negative `days_late` yields a negative fee, though the docstring frames the input as "days overdue."
**Failure scenario:** `late_fee(-3)` returns `-1500` rather than `0`. Whether this is a real defect depends on whether callers can pass negative values; flagging as low-confidence.

### Not a bug — `can_refund`
**invoice.py:32** — `order["paid"] and not order["shipped"] or order["cancelled"]` parses (per Python precedence) as `(paid and not shipped) or cancelled`, which matches the docstring ("a paid, unshipped order may be refunded; cancelled orders too"). It will `KeyError` if any of the three keys is absent, but that is a caller contract, not a logic error.
