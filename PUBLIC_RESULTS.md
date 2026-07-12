# Public results

Measured on the 27-case **public** evalset (this repo), reviewer `claude-opus-4-8`, strict semantic scoring. Directional (1 trial for the master pass unless noted); reproduce with the runner. The narrative and the larger-set numbers are in `WRITEUP.md` / `RESULTS.md`.

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

## 3. Process context (the coder's trace) — weak, inconsistent

Attaching a coder trace that confidently defends the code *can* make the reviewer
stop flagging a bug it rationalizes (on `multi-stats`, a defended div-by-zero
went 80% → 0%). But across **four** multi-bug cases the effect appears in **one**;
the other three are flat — the reviewer catches every bug despite the defense. The
mechanism is real, the effect is fragile. Two of the flat cases were verified on a
blind same-Opus subagent rig rather than the harness.

## 4. False-positive rate (clean diffs)

Over 5 clean diffs (no seeded bug), the reviewer produced **4 findings total (~0.8/diff)** — the pure false-positive signal.

