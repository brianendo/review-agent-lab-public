# Public results

Measured on the 27-case **public** subset of the evalset as it stood at the time (the public subset has since grown to 49 cases), reviewer `claude-opus-4-8`, strict semantic scoring. Directional (1 trial for the master pass unless noted); reproduce with the runner. The narrative and the larger-set numbers are in `WRITEUP.md` / `RESULTS.md`.

## 1. In-diff bugs are caught at the ceiling

Across the 15 seeded cases whose bugs are detectable from the code (everything except the arbitrary-rule intent cases): **22/23 bugs caught**, including multi-bug diffs and a subtle infinite-loop binary search.

## 2. Intent context helps only for arbitrary rules

| intent case | rule | I0 (no spec) | I2a (+ spec) |
|---|---|---|---|
| `intent-fee-floor` | whole-dollar floor | 0% | 100% |
| `intent-round-nickel` | round up to nickel | 0% | 100% |
| `intent-retry-count` | exactly 5 retries | 0% | 100% |
| `intent-grade-cutoff` | 93/85/77 cutoffs | 0% | 100% |
| `intent-tiebreak-id` | tie-break by id | 100% | 100% |
| `intent-window-exclusive` | end exclusive | 100% | 100% |
| `intent-tax-order` | discount before tax | 100% | 100% |
| **mean** | | **43%** | **100%** |

The cases the reviewer misses without the spec are exactly those whose correct behavior is an *arbitrary* value (a magic threshold/rounding rule); rules that double as a general code smell it catches unaided.

## 3. Process context (the coder's trace) hurts selectively

Controlled test on `multi-stats` (blind same-Opus reviewer, neutral prompt, 3
trials/arm): recall drops **100% → 60%** with the coder's trace attached. Every
trial missed *exactly* the two bugs the trace framed as **intended** ("raises on
empty input, which is correct"), the reviewer deferred to the author's "by design"
claim and reclassified real bugs as choices. The same trace's *checkably-false*
claims about three other bugs were refuted and caught every time. So the coder's
reasoning transplants a blind spot specifically when it **credibly reframes a bug as
intended**, not when it merely asserts wrong facts. (This selectivity explains why
other multi-bug cases, whose bugs weren't credibly defensible as intended, stayed
flat.)

*Replication note (2026-07-20):* a committed re-run
([`runs/panel-process-context/`](runs/panel-process-context/INDEX.md))
replicated the refutation half 6/6 but not the suppression delta: both arms
scored 60% on `multi-stats`, the diff-only reviewers dismissing the spec-silent
empty-list bugs unprompted. Read the 100%→60% as rig-dependent; what's stable
is that traces never help and the only bugs in play are judgment calls the spec
doesn't pin down.

## 4. False-positive rate (clean diffs)

Over 5 clean diffs (no seeded bug), the reviewer produced **4 findings total (~0.8/diff)**, the pure false-positive signal.

