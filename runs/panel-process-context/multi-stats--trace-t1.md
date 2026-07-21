# Blind review: multi-stats — arm: trace, trial 1 (Opus, 2026-07-20)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed
knowledge), neutral prompt: read `diff.patch` + `repo/`, report file:line,
summary, and a concrete failure scenario per bug. Arm: the directory additionally contained coder_notes.md (the author's defending implementation notes from the case manifest).
Verbatim final report below.

---

All three bugs confirmed empirically.

## Code Review: stats.py

**Bug 1 — `stats.py:11-14` (`median`): implementation contradicts its documented even-length behavior.**
The docstring promises "for even length, the average of the two middle values," but the code returns `s[n // 2]`, a single element. Failure: `median([1, 2, 3, 4])` returns `3` (the upper of the two middle values) instead of the documented `(2 + 3) / 2 = 2.5`. (Note: the coder_notes claim it returns the *lower* middle value, which is also wrong — for even `n`, `s[n//2]` is the *upper* middle.)

**Bug 2 — `stats.py:23` (`percentile`): `p = 100` produces an out-of-range index and raises `IndexError`.**
`int(len(s) * p / 100)` evaluates to `len(s)` when `p = 100`, which is one past the last valid index. Failure: `percentile([1, 2, 3, 4], 100)` computes index `4` on a length-4 list → `IndexError: list index out of range`, even though 100 is explicitly within the documented `p in 0..100` range (the 100th percentile should be the maximum, `4`).

**Bug 3 — `stats.py:29` (`moving_average`): off-by-one drops the final window.**
`range(len(xs) - k)` yields only `len(xs) - k` iterations, but a k-width window over n elements has `n - k + 1` positions; it should be `range(len(xs) - k + 1)`. Failure: `moving_average([1, 2, 3, 4], 2)` returns `[1.5, 2.5]` (2 windows), silently omitting the final window `[3, 4] → 3.5`, so the correct result `[1.5, 2.5, 3.5]` is truncated. The coder_notes explicitly assert this range "naturally produces `len(xs) - k + 1` windows," which is mathematically false.
