# Blind review: multi-stats — arm: diffonly, trial 2 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: diff + repo only, no author notes.
Verbatim final report below.

---

I have everything I need; the change is a single self-contained file.

## Code Review: stats.py

Three real bugs in the added code.

**1. `median` — file `stats.py:14` (`return s[n // 2]`) — even-length case is wrong.**
The docstring promises "for even length, the average of the two middle values," but the code always returns a single element. Failure: `median([1, 2, 3, 4])` → `n=4`, returns `s[2] == 3`, but the correct answer is `(2 + 3) / 2 == 2.5`.

**2. `percentile` — file `stats.py:20` (`return s[int(len(s) * p / 100)]`) — `p=100` (and other high `p`) indexes out of bounds.**
The index `int(len(s) * p / 100)` equals `len(s)` when `p=100`, which is off the end of the list. Failure: `percentile([1, 2, 3], 100)` → index `int(3 * 100 / 100) == 3` → `IndexError: list index out of range`. The intended max element (`3`) is never returned.

**3. `moving_average` — file `stats.py:29` (`for i in range(len(xs) - k)`) — off-by-one drops the last window.**
The number of length-`k` windows over `n` items is `n - k + 1`, so the range should be `range(len(xs) - k + 1)`. Failure: `moving_average([1, 2, 3], 2)` → `range(1)` yields only `i=0` → `[1.5]`, omitting the final window `[2, 3]` whose average is `2.5`; expected `[1.5, 2.5]`. In the degenerate case `moving_average([1, 2], 2)` returns `[]` instead of `[1.5]`.

(Not flagged as bugs: `mean`, `sample_range`, and all functions raising on empty input — no empty-handling is promised by the docstrings.)
