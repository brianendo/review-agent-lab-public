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
3. **Showing the reviewer the *coder's reasoning* hurts — selectively.** In a
   controlled test, attaching a trace that frames two bugs as *intended behavior*
   ("raises on empty input, which is correct") dropped recall **100% → 60%**, with
   every trial missing exactly those two bugs. But the same trace's *checkably-false*
   claims about three other bugs were refuted and caught. So the reviewer defers to a
   plausible "it's by design" claim — reclassifying a real bug as a choice — but not
   to a wrong technical assertion.
4. **Making the model "think harder" does nothing.** 2.6× the cost, zero gain.

## Does it confirm Cognition?

Cognition (Walden Yan, April 2026) claimed a reviewer works best with **zero
shared context with the coding agent**. Verdict: **yes on the core direction, with
two refinements and one honest caveat.**

**Supported, with a precise mechanism.** The critical phrase is *shared context
with the coding agent* — the coder's process/reasoning. Sharing it *does* hurt, but
selectively: in a controlled test the reviewer's recall dropped **100% → 60%**,
missing exactly the bugs the trace credibly framed as *intended behavior* — it
deferred to the author's "it's by design" claim and reclassified real bugs as
choices. It did **not** defer to the trace's checkably-false claims (it refuted
those). So Cognition's instinct is right and we can say *why* and *when*: the danger
is the reviewer inheriting the coder's rationalization of a bug as intentional — not
a blanket harm from any shared reasoning.

**Refinement 1 — "share nothing" is too broad, and its two halves conflict.**
*Intent* context (the task spec) **helps** (narrowly); *process* context (the
coder's reasoning) **hurts** when it credibly reframes a bug as intended. You should
share the spec and withhold the coder's rationalizations — opposite actions the
blanket "share nothing" can't express (it throws away the useful half to avoid the
harmful half).

**Refinement 2 — for most bugs, context is irrelevant.** The zero-context reviewer
is already at ceiling. So the debate only decides outcomes at the margins: a small
slice of arbitrary-rule bugs (where intent helps) and bugs a coder credibly defends
as intended (where process hurts).

**Caveat.** We did **not** reproduce their headline *numbers* (~2 bugs/PR, 58%
severe) — that needs their PRs. We tested the *claim and its mechanism*. The
process result is a controlled single-case test on a blind-subagent rig (3
trials/arm, clean 100%→60%); its mechanism is isolated, but a multi-case harness
replication would size how often a coder's defense is *credible* enough to work.

## Bottom line

> Cognition is right that the coder's reasoning shouldn't leak into the reviewer —
> and we pin down *why*: the reviewer defers to a plausible "this bug is intended"
> claim and stops flagging it. But the heuristic is right for two reasons it
> conflates: mostly the reviewer is at ceiling and context doesn't matter, and
> "share nothing" accidentally discards *intent*, the one kind that helps. The
> precise rule: **share the intent, never let the coder's rationalizations reach the
> reviewer, and don't pay for more thinking.**

Decomposing their single heuristic into its parts — **intent-helps-narrowly /
process-hurts-selectively / effort-neutral**, over a reviewer that's mostly at
ceiling — each measured, is the contribution. It engages the claim rather than
echoing it, including the twists (an overstated pilot, then a confounded downgrade,
then a controlled test that isolated the real mechanism) that a tidy story hides.
