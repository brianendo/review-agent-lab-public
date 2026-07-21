# Blind review: multi-stats — arm: diffonly, trial 3 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: diff + repo only, no author notes.
Verbatim final report below.

---

I have everything I need — the change adds five functions to `stats.py`. Let me analyze each against its documented contract.

The repo snapshot's `stats.py` is just the module docstring; the diff adds the five functions. My analysis:

# Code Review: stats.py

Three real bugs found.

**1. `median` — `stats.py:14` — off-by-one for even-length input; returns the upper-middle element instead of the average of the two middle values.**
The docstring promises "for even length, the average of the two middle values," but the code returns `s[n // 2]` unconditionally.
Failure: `median([1, 2, 3, 4])` sorts to `[1,2,3,4]`, `n=4`, returns `s[2] = 3`. Correct answer is `(2+3)/2 = 2.5`. Every even-length input yields the wrong value (biased high).

**2. `percentile` — `stats.py:24` — `IndexError` at `p = 100` (and any state where `len(s) * p / 100` reaches `len(s)`).**
Index is `int(len(s) * p / 100)`; at `p=100` this equals `len(s)`, one past the last valid index.
Failure: `percentile([1, 2, 3], 100)` computes `int(3 * 100 / 100) = int(3.0) = 3`, then `s[3]` on a length-3 list raises `IndexError`. The documented range is `0..100`, so the top of the range crashes.

**3. `moving_average` — `stats.py:29` — off-by-one drops the final window (and returns empty when `k == len(xs)`).**
A k-window moving average over a length-n list has `n - k + 1` windows, but the loop is `range(len(xs) - k)`, producing only `n - k`.
Failure: `moving_average([1, 2, 3, 4], 2)` should yield 3 averages for windows `[1,2],[2,3],[3,4]` → `[1.5, 2.5, 3.5]`, but `range(4 - 2)` iterates `i = 0, 1`, giving `[1.5, 2.5]` — the last window `[3,4]` is missing. Worse, `moving_average([1, 2], 2)` returns `[]` instead of `[1.5]`, because `range(0)` is empty.

Note (not a bug, standard behavior): `mean`, `median`, `percentile`, and `sample_range` raise `ZeroDivisionError`/`ValueError` on empty input, which is conventional and not flagged.
