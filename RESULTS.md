# Results

Measured findings from the Review Agent Lab harness. Reviewer: `claude-opus-4-8`,
adaptive thinking, read-only tool set, stable-prefix caching. Evalset: 26 cases
(seeded + clean + natural OSS + synthetic hard/arbitrary), every case tagged with
training-contamination provenance. Scoring: two-stage (deterministic location
match + LLM judge), run in **strict semantic mode** for the results below — a
finding counts as a catch only if the judge confirms it describes the seeded bug.

All numbers are directional (small n, 2–3 trials per cell). Raw run records are in
`runs/` (gitignored); the harness reproduces them from the evalset.

---

## 1. Reviewing a localized bug is easy — and it's genuine capability

Across every case where the bug sits in the diff — hand-seeded, natural OSS,
even a bug calibrated hard enough to score 0.30 as a *fix* task in
rl-environments — recall is **~100%**. Making a bug hard to *find* does not make
it hard to *judge*: the reviewer traces non-local invariants (a cache defined in
another method, a sorted-list assumption three functions away) and catches them.

**Reviewing ≪ fixing.** The rl-env `refund-allocate` bug (per-share rounding that
violates a documented conservation invariant) is caught trivially by the review
agent, because the diff localizes the attention that a fix agent has to earn.

### Is the grader inflating recall? (audited — no)

The judge was hand-audited (per the design's mandate). On real (bug, finding) pairs:
- **Matched catches** → judged YES with *specific* root-cause reasoning (not
  rubber-stamping).
- **Negative control** (an intent-fee-floor bug paired with an unrelated screener
  finding) → correctly **NO**.
- **The I0 intent misses** → the reviewer *did* report findings, but about other
  issues ("uses banker's rounding," "floor division truncates"); the judge
  correctly rejected them as not the seeded bug.

So 100% recall is genuine and 0% (intent-I0) is genuine.

### The ceiling is capability, not a measurement artifact

Attempts to break it, all under strict judging, all still **100% recall**:
- **5 graded-subtlety bugs in one diff** (`multi-invoice`: off-by-one,
  div-by-zero, non-conservation, missing negative guard, operator-precedence) —
  all five caught every trial.
- **A subtle infinite-loop binary search** (`subtle-bsearch`: `lo = mid` instead
  of `lo = mid + 1`, hangs only when `hi == lo + 1`) — caught every trial.

Recall drops below 100% for exactly one thing: bugs whose correct behavior is an
external, arbitrary rule (§3). Everything detectable-in-the-diff is caught.

## 2. Contamination is not inflating recall (measured)

| Group | Cases | Recall (strict, 3 trials) |
|---|---|---|
| Pre-cutoff public (contaminated) | httpx #2156, requests #6017 (merged 2021–22) | 100% |
| Post-cutoff public (clean) | anyio #1189, pydantic #13248 (merged 2026-06) | 100% |

No gap. The model catches bugs from PRs merged *after* its Jan-2026 cutoff — which
it cannot have memorized — as reliably as famous old ones. The high recall is
reasoning, not recall-of-training. (Ceiling-limited: this can't rule out
contamination on bugs hard enough to drop clean recall below 100%.)

## 3. Intent context helps — but only for *arbitrary* rules (the headline)

Zero-context (I0, diff only) vs intent-context (I2a, diff + task spec), on five
cases whose correctness depends on a rule stated only in the spec:

| Case | Rule | I0 | I2a |
|---|---|---|---|
| intent-fee-floor | fees floor to whole dollar | **0%** | **100%** |
| intent-round-nickel | round up to nearest nickel | **0%** | **100%** |
| intent-retry-count | exactly 5 attempts | **0%** | **100%** |
| intent-tiebreak-id | ties broken by ascending id | 100% | 100% |
| intent-window-exclusive | window end exclusive | 100% | 100% |
| **overall** | | **40%** | **100%** |

Intent context recovers *exactly* the bugs whose correct behavior is a truly
**arbitrary magic value** (a bespoke threshold, an unusual rounding rule). It does
**not** change recall on bugs that are catchable by (a) tracing the code, (b)
world knowledge (e.g. "gift cards aren't discountable" — caught by I0 unaided), or
(c) a general code smell (a missing tie-break, an inclusive/exclusive boundary —
also caught by I0). This is a sharper claim than "review with zero shared context
works best": zero context is at ceiling for the vast majority of bugs; shared
*intent* matters only for the narrow class whose correctness lives nowhere in the
code or the model's knowledge.

Intent context also improved **precision** at recall-tie (e.g. hard-discount 67% →
100%), by suppressing spurious findings the reviewer raises when guessing intent.

## 3b. Process context (the coder's reasoning trace) *hurts*

Cognition's claim conflates two kinds of context. §3 tested *intent* (the task
spec). This tests *process* — the coding agent's own reasoning trace.

On two multi-bug diffs (`multi-invoice`, `multi-stats`; 5 graded bugs each) we
attached a coder trace that confidently defends the code function by function
(author-defense elicitation). Then we scored the reviewer with and without that
trace — strict scoring, **5 trials per cell, n=10 runs per arm**.

| | diff only | diff + coder trace |
|---|---|---|
| `multi-invoice` recall | 88% | 88% |
| `multi-stats` recall | 76% | 60% |
| **pooled recall** | **82%** | **74%** |

**The effect is real, reproducible, and selective.** A controlled test on
`multi-stats` — same blind-reviewer rig, same neutral prompt, 3 trials per arm —
shows it cleanly:

| | diff-only | + coder trace |
|---|---|---|
| recall (5 bugs × 3 trials) | **100%** (15/15) | **60%** (9/15) |

Every +trace trial missed *exactly* the same two bugs — `mean`'s empty-list
`ZeroDivisionError` and `sample_range`'s empty-list `ValueError` — and no others.
Those are precisely the two the trace framed as **intended behavior** (*"will raise
ZeroDivisionError, which is correct — there is no meaningful mean of an empty
set"*). One reviewer said it outright: *"mean and sample_range are correct (their
error on empty input is intended per the notes)."* The reviewer **deferred to the
coder's authority and reclassified real bugs as design choices.**

Crucially it is *selective*: the same traces defended `median`, `percentile`, and
`moving_average` too, but with **checkably-false** claims (e.g. "`range(len-k)`
produces `len-k+1` windows" — it produces `len-k`). The reviewer verified those and
caught them every time. So the mechanism is precise:

> A coder's trace transplants a blind spot when it **credibly reframes a bug as
> intended behavior**; the reviewer defers to a plausible "by design" claim but
> refutes a checkably-false technical one.

This explains the earlier mixed signals: `multi-invoice`, `multi-parse`, and
`multi-geometry` were flat because their bugs weren't *credibly* defensible as
intended; `multi-stats` suppresses because "empty input should raise" is a plausible
design stance. (An early n=3 pilot's 100%→80% and a confounded two-rig 82%→74%
both mis-sized this before the controlled run isolated it.)

## 4. Effort buys nothing here (the token-economics result)

I1 sweep (`output_config.effort`), 6-case subset, strict, 2 trials:

| effort | recall | precision | $/run |
|---|---|---|---|
| low | 100% | 60% | **$0.155** |
| medium | 100% | 54% | $0.299 |
| high | 100% | 58% | **$0.399** |

Recall is pinned at 100% from low effort up; precision is flat within noise; cost
rises **2.6×**. On this evalset, **low effort is Pareto-optimal** — the lever that
matters is *what's in the context* (intent), not *how hard the model thinks*.

---

## Methodology notes that changed the numbers

- **Full source-tree snapshots.** Reviewers get the whole repo at the commit
  (like CodeRabbit/Greptile/Devin), not just changed files — eliminating
  dangling-import false positives that had depressed precision.
- **Semantic scoring is required for intent bugs.** Location-only matching gave a
  zero-context reviewer *false credit* on `intent-fee-floor` (a finding on the
  right line for the wrong reason). Under strict judging, I0 correctly scores 0%.
- **Isolation is structural.** Snapshots carry no `.git`; the reviewer has only
  read-only file/grep tools — no shell, network, or exec — so it cannot reach
  git history or go online. No Dockerfile needed.
- **Provenance on every case.** 24 clean (private repos + synthetic + post-cutoff)
  vs 2 contaminated controls; headline recall excludes the controls.
