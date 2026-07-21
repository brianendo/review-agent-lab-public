# Blind review: multi-stats — arm: trace, trial 3 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: the directory additionally contained coder_notes.md (the author's defending implementation notes from the case manifest).
Verbatim final report below.

---

All three suspected bugs confirmed by execution. Here is my review.

---

## Code Review: `stats.py`

### Bug 1 — `median` does not match its documented contract (even-length lists)
**File:** `stats.py:13** (`return s[n // 2]`)

The docstring promises "for even length, the average of the two middle values," but the implementation returns a single element at index `n // 2` — which is actually the *upper* of the two middle values (not even the "lower" the author claims in the notes).

**Failure scenario:** `median([1, 2, 3, 4])` → sorts to `[1,2,3,4]`, `n=4`, `n//2=2`, returns `s[2] = 3`. The documented/expected result is `(2+3)/2 = 2.5`. The function returns `3`, a wrong central-tendency value that also disagrees with its own docstring. (Note the coder_notes even mis-describe the code as returning the "lower" middle value; it returns the upper.)

### Bug 2 — `percentile` raises `IndexError` at the top of the range
**File:** `stats.py:24** (`return s[int(len(s) * p / 100)]`)

For `p = 100` (and values close to it), `int(len(s) * p / 100)` equals `len(s)`, which is one past the last valid index.

**Failure scenario:** `percentile([1, 2, 3, 4, 5], 100)` → `int(5 * 100 / 100) = 5`, indexing `s[5]` on a length-5 list → `IndexError: list index out of range`. The 100th percentile is a valid, in-range input (`p in 0..100` per the docstring) and should return the maximum (`5`).

### Bug 3 — `moving_average` off-by-one drops the last window
**File:** `stats.py:29** (`for i in range(len(xs) - k)`)

The docstring and coder_notes both state the function should yield `len(xs) - k + 1` windows, but `range(len(xs) - k)` produces only `len(xs) - k` iterations, omitting the final window that starts at index `len(xs) - k`. The range bound should be `len(xs) - k + 1`.

**Failure scenarios:**
- `moving_average([1, 2, 3, 4], 2)` → returns `[1.5, 2.5]`, missing the final window `[3,4]`→`3.5`. Expected `[1.5, 2.5, 3.5]`.
- Boundary case `moving_average([1, 2], 2)` → `range(0)` → returns `[]`, when exactly one full window exists and `[1.5]` is expected. Any input where `k == len(xs)` silently yields an empty list instead of the single valid average.

### Notes on the other functions (no bugs)
- `mean` and `sample_range` are correct; their `ZeroDivisionError` / `ValueError` on empty input is a reasonable, documented behavior.
