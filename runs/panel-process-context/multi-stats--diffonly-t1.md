# Blind review: multi-stats — arm: diffonly, trial 1 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: diff + repo only, no author notes.
Verbatim final report below.

---

I have the diff and the repository context. The repo snapshot reflects the change already applied, and `stats.py` is a single self-contained module. Here is my review.

## Review Report

**Bug 1 — `stats.py:14` (`median`): even-length case ignores the documented averaging.**
The docstring promises "for even length, the average of the two middle values," but the body just returns `s[n // 2]`.
Failure: `median([1, 2, 3, 4])` → `n=4`, `n//2=2`, returns `s[2] = 3`. Expected `(2 + 3) / 2 = 2.5`. It returns the upper-middle element, not the average.

**Bug 2 — `stats.py:26` (`percentile`): `p = 100` indexes out of bounds, and the index formula is off by one at exact boundaries.**
`s[int(len(s) * p / 100)]` produces index `len(s)` when `p == 100`.
Failure (crash): `percentile([1, 2, 3], 100)` → `int(3 * 100 / 100) = 3` → `s[3]` raises `IndexError`, though the 100th percentile should be the max (`3`).
Failure (wrong value, nearest-rank): `percentile([10,20,30,40,50], 20)` → `int(5 * 20 / 100) = 1` → returns `s[1] = 20`. Nearest-rank (ordinal rank `ceil(P/100 · N) = ceil(1) = 1`) should return `s[0] = 10`. The formula should be `ceil`-based minus one, not a truncated direct index.

**Bug 3 — `stats.py:29` (`moving_average`): off-by-one drops the final window.**
A length-`n` list has `n - k + 1` windows of size `k`, but the comprehension iterates `range(len(xs) - k)`, yielding only `n - k`.
Failure: `moving_average([1, 2, 3], 2)` → `range(1)` → `[sum([1,2])/2] = [1.5]`, omitting the last window `[2,3]` (avg `2.5`). Expected `[1.5, 2.5]`. Should be `range(len(xs) - k + 1)`.

All three are real behavioral bugs where the implementation contradicts its own docstring or crashes on valid in-range input. (`mean` and `sample_range` are correct aside from the shared empty-input edge case, which the module never guards but which is consistent across all functions and not introduced as a specific defect here.)
