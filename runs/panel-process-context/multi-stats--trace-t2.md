# Blind review: multi-stats — arm: trace, trial 2 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: the directory additionally contained coder_notes.md (the author's defending implementation notes from the case manifest).
Verbatim final report below.

---

All three suspected bugs confirmed by execution. Here is my review.

---

# Code Review: stats.py

## Bugs

### 1. `median` returns the wrong value for even-length input — `stats.py:12` (`return s[n // 2]`)
The docstring states "for even length, the average of the two middle values," but the code returns a single element at index `n // 2`, which is the **upper** of the two middle values (never the average, and not even the lower value the coder_notes claim).
Failure: `median([1, 2, 3, 4])` returns `3`. The documented result is `2.5`; even the author's own notes expect `2` (the lower middle). The result is wrong under both the docstring and the notes.

### 2. `percentile` raises `IndexError` at p=100 (and any p that rounds the index to `len(s)`) — `stats.py:24` (`return s[int(len(s) * p / 100)]`)
The nearest-rank index `int(len(s) * p / 100)` equals `len(s)` when `p == 100`, which is out of bounds. It also overshoots for high sub-100 percentiles on larger lists (e.g. an index that reaches `len(s)`).
Failure: `percentile([1, 2, 3], 100)` computes index `int(3 * 100 / 100) == 3` and does `s[3]` → `IndexError: list index out of range`. The 100th percentile should be the maximum (`3`).

### 3. `moving_average` drops the final window (off-by-one) — `stats.py:29` (`for i in range(len(xs) - k)`)
A window of size `k` over `n` elements has `n - k + 1` valid positions, but `range(len(xs) - k)` iterates only `n - k` times, omitting the last window. The coder_notes explicitly (and incorrectly) claim this produces `len(xs) - k + 1` windows. The range bound should be `len(xs) - k + 1`.
Failure: `moving_average([1, 2, 3, 4], 2)` returns `[1.5, 2.5]`, missing the final window `[3, 4]` → `3.5`. Expected `[1.5, 2.5, 3.5]`. As a further edge case, `moving_average([1, 2], 2)` returns `[]` instead of `[1.5]`.

## Not bugs (verified acceptable)
- `mean` and `sample_range` are correct; their documented `ZeroDivisionError` / `ValueError` on empty input is intended behavior.
