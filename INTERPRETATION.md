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
3. **Showing the reviewer the *coder's reasoning* can hurt — but weakly and
   rarely.** With the coder's confident rationale attached, the reviewer sometimes
   stops flagging a bug the trace defends (a div-by-zero: 80% → 0%). But this
   happened in only **1 of 4** multi-bug cases tested; in the other three the
   reviewer caught every bug despite the defense. The mechanism is real; the
   effect is fragile.
4. **Making the model "think harder" does nothing.** 2.6× the cost, zero gain.

## Does it confirm Cognition?

Cognition (Walden Yan, April 2026) claimed a reviewer works best with **zero
shared context with the coding agent**. Verdict: **yes on the core direction, with
two refinements and one honest caveat.**

**Partly supported (direction), but weakly.** The critical phrase is *shared
context with the coding agent* — the coder's process/reasoning. We found the
predicted direction — sharing the coder's reasoning *can* hurt: on one case the
reviewer stopped flagging a bug the trace defends (80% → 0%). But the effect
appeared in only **1 of 4** multi-bug cases; usually the reviewer stayed robust.
So the mechanism behind Cognition's heuristic exists, but our evidence that it
*reliably* hurts is thin. The stronger reason "share nothing" works is simply that
the reviewer is at ceiling with or without context (finding 1).

**Refinement 1 — "share nothing" is too broad.** *Intent* context (the task spec)
is different from *process* context (the coder's reasoning). Intent **helps**
(narrowly); process only *sometimes* hurts (1 of 4 cases). You should share the
spec regardless; skip the coder's session because it doesn't help, not because it
reliably hurts. Cognition lumps these together and discards the useful half.

**Refinement 2 — for most bugs, context is irrelevant.** The zero-context reviewer
is already at ceiling. So the entire "shared context" debate only decides outcomes
at the margins: a small slice of arbitrary-rule bugs (where intent helps) and the
occasional bug a coder's confident defense talks the reviewer out of flagging.

**Caveat.** We did **not** reproduce their headline *numbers* (~2 bugs/PR, 58%
severe) — that needs their PRs and setup. We tested the *claim and its mechanism*
on our own evalset. The process-context effect is weak and inconsistent (present
in 1 of 4 multi-bug cases; two of the flat cases were reviewed on a blind-subagent
rig, not the byte-controlled harness) — the mechanism is demonstrated, its
reliability is not.

## Bottom line

> Cognition's instinct that the coder's reasoning shouldn't leak into the reviewer
> points the right way, but our evidence that it *reliably* hurts is thin — it hurt
> in only 1 of 4 cases. "Zero shared context" mostly works for a different reason:
> the reviewer is already at ceiling without any context, and the heuristic
> accidentally discards *intent* context, the one kind that helps. The precise
> rule: **share the intent, skip the reasoning (it rarely helps, occasionally
> hurts), and don't pay for more thinking — and know that most of the time it
> doesn't matter because the reviewer is at ceiling.**

Decomposing their single heuristic into its parts — **intent-helps-narrowly /
process-hurts-weakly / effort-neutral**, over a reviewer that's mostly at ceiling —
each measured, is the contribution. It engages the claim rather than echoing it,
including where the evidence turned out weaker than the tidy version.
