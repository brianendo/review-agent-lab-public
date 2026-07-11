# What the results mean — and do they confirm Cognition?

Plain-language reading of the measured findings (numbers and tables in
`RESULTS.md`; full narrative in `WRITEUP.md`).

## What the results actually say

Four findings, one story:

1. **Reviewing is easy; the bug just has to be in the diff.** A zero-context
   reviewer with full repo access catches ~100% of bugs that are detectable from
   the code — subtle ones, several-at-once, and non-local ones, even a bug that is
   "hard" for a *fixing* agent. This is genuine capability: we controlled for
   training-data memorization (post-cutoff bugs are caught just as well) and
   hand-audited the grader.
2. **Telling the reviewer the *intent* (what the change was supposed to do) helps —
   but rarely.** It only matters for bugs whose correctness is an *arbitrary rule*
   not present in the code or in general knowledge (a magic threshold, a bespoke
   rounding rule). For everything else the reviewer is already at ceiling, so
   intent adds nothing.
3. **Showing the reviewer the *coder's reasoning* hurts (modestly).** With the
   coder's confident rationale attached, recall dropped 82% → 74% across two
   multi-bug diffs (n=10/arm): the reviewer inherited the coder's blind spot and
   stopped flagging specific bugs the trace defended (a div-by-zero: 80% → 0%).
4. **Making the model "think harder" does nothing.** 2.6× the cost, zero gain.

## Does it confirm Cognition?

Cognition (Walden Yan, April 2026) claimed a reviewer works best with **zero
shared context with the coding agent**. Verdict: **yes on the core direction, with
two refinements and one honest caveat.**

**Confirmed (direction).** The critical phrase is *shared context with the coding
agent* — the coder's process/reasoning. Our I2b result directly supports it:
sharing the coder's reasoning trace measurably *hurt* the reviewer (recall 82% →
74%, n=10/arm). The mechanism behind their heuristic checks out, and we name the
mechanism they didn't: the reviewer defers to the coder's rationalization of a
specific bug (an empty-list crash the trace defends: caught 80% → 0%).

**Refinement 1 — "share nothing" is too broad.** *Intent* context (the task spec)
is different from *process* context (the coder's reasoning). Intent **helps**
(narrowly); process **hurts**. You should share the spec, just not the coder's
session. Cognition lumps these together and discards the useful half.

**Refinement 2 — for most bugs, context is irrelevant.** The zero-context reviewer
is already at ceiling. So the entire "shared context" debate only decides outcomes
at the margins: a small slice of arbitrary-rule bugs (where intent helps) and
subtle bugs (where process hurts).

**Caveat.** We did **not** reproduce their headline *numbers* (~2 bugs/PR, 58%
severe) — that needs their PRs and setup. We tested the *claim and its mechanism*
on our own evalset. The process-context result is directional (two cases, 5 trials,
a model-elicited author-defense trace); it demonstrates the effect cleanly but
wants a bigger sample to size it.

## Bottom line

> Cognition is right that sharing the coder's reasoning with the reviewer is
> harmful — and we show *why*. But "zero shared context" is right for the wrong
> reason: it works mostly because the reviewer is already at ceiling without any
> context, and it accidentally discards *intent* context, the one kind that helps.
> The precise rule is: **share the intent, never the reasoning, and don't pay for
> more thinking.**

Decomposing their single heuristic into **intent-helps / process-hurts /
effort-neutral**, each measured, is the contribution — it engages the claim rather
than echoing it.
