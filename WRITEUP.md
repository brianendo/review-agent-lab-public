# When does context help a code-review agent? A measured answer.

*A code-review agent harness, run through controlled iterations against a
seeded-bug evalset, with an honest methodology attached to every number.*

## Why this exists

In April 2026, Cognition's Walden Yan argued that a code-review agent works best
with **zero shared context** with the coding agent that wrote the change. The
claim came with headline numbers (~2 bugs per PR, 58% severe) but **no published
methodology** — no evalset, no scorer, no error bars. This project publishes one,
and in doing so arrives at a sharper claim than the original.

The thesis, in one line: **for the vast majority of bugs, a zero-context reviewer
with repo access is already at ceiling; shared context only changes the outcome
for a narrow, identifiable class of bugs — and even then, only *intent* context
helps, not more reasoning effort.**

## The rig

A custom agent loop on the Anthropic Messages API (`claude-opus-4-8`, adaptive
thinking), built on the SDK's tool runner so that **context assembly — the
experiment variable — stays under byte-level control**. The reviewer has a fixed,
poka-yoke'd, read-only tool set: `read_file`, `list_files`, `grep_repo`,
`get_diff`, and a single strict-schema `report_finding`. No bash, no network, no
exec.

- **Evalset (28 cases):** real diffs from private repos with hand-seeded bugs,
  natural bugs reversed out of real OSS fix-PRs, a calibrated-hard bug borrowed
  from an RL-environments task, and synthetic cases engineered for specific
  difficulty. Six clean diffs (no seeded bug) measure the false-positive rate.
- **Full source-tree snapshots.** The reviewer gets the *entire* repository at the
  commit — like CodeRabbit, Greptile, or Devin — not just the changed files.
- **Two-stage scorer.** Deterministic location match, then an LLM judge, run in a
  **strict semantic mode**: a finding counts as a catch only if the judge
  confirms it describes the seeded bug — not merely that it landed on the right
  line. The judge was hand-audited for calibration.
- **Provenance on every case.** Each case is tagged clean vs. contaminated against
  the model's Jan-2026 knowledge cutoff.

## What we found

### 1. Reviewing is far easier than fixing.

Every bug that sits in the diff is caught at ~100% recall — hand-seeded, natural,
multi-bug, or subtle. A bug calibrated to score **0.30 as a *fix* task** (it needs
non-local investigation, tacit conventions, and a correct algorithm) is caught
**trivially** as a *review* task, because the diff localizes the attention the
fixer has to earn. Difficulty-to-find ≠ difficulty-to-judge.

### 2. The high recall is genuine capability, not memorization.

A contamination control — bugs from PRs merged *after* the model's cutoff, which
it cannot have seen — is caught **just as reliably** (100%) as famous pre-cutoff
bugs. And the grader was audited: matched catches judged YES with specific
reasoning, unrelated pairings judged NO, and the intent-misses correctly rejected.

### 3. Intent context helps — but *only* for arbitrary rules.

Zero-context (diff only) vs. intent-context (diff + task spec), strict scoring:

| Bug's correctness depends on… | Zero-context | + Intent |
|---|---|---|
| an **arbitrary rule** (whole-dollar floor, round-to-nickel, exact-5-retries) | **0%** | **100%** |
| a general code smell (missing tie-break, inclusive/exclusive boundary) | 100% | 100% |
| domain knowledge ("gift cards aren't discountable") | 100% | 100% |
| tracing the code (cache invalidation, sorted-list invariant) | 100% | 100% |

Intent context recovers **exactly** the bugs whose correct behavior is a magic
value that lives nowhere in the code and isn't in the model's world knowledge. For
everything else, the zero-context reviewer is already at ceiling. Intent context
also improved **precision** at recall-tie (fewer spurious findings from guessing
intent).

### 4. Process context — the coder's reasoning trace — hurts *selectively*.

Intent (§3) and *process* are different context. Attaching the coder's own reasoning
trace tests whether the reviewer inherits its blind spots. A controlled run on
`multi-stats` (same blind-reviewer rig, same neutral prompt, 3 trials/arm) is clean:
recall drops **100% → 60%**, and every +trace trial missed *exactly* the same two
bugs — the empty-list crashes the trace framed as *intended* (*"raises
ZeroDivisionError, which is correct"*). One reviewer wrote: *"mean and sample_range
are correct — their error on empty input is intended per the notes."* It deferred to
the author's authority and reclassified real bugs as design choices. But it is
**selective**: the same trace defended three other bugs with *checkably-false* claims
(e.g. "`range(len−k)` produces `len−k+1` windows"), and the reviewer refuted and
caught all three. So process context transplants a blind spot **specifically when it
credibly reframes a bug as intended behavior** — not when it merely asserts wrong
facts. (An early pilot's 100→80 and a confounded two-rig 82→74 mis-sized this; the
controlled test isolated the real, selective mechanism.)

### 5. Reasoning effort is wasted spend.

Sweeping `output_config.effort` low → high: recall pinned at 100% from low effort,
precision flat within noise, **cost up 2.6×**. On this evalset, **low effort is
Pareto-optimal**. The lever that matters is *what's in the context*, not *how hard
the model thinks*.

## The refined claim

Cognition said: *review with zero shared context works best.* The measured
refinement:

> A zero-context reviewer with full repo access is at ceiling for essentially all
> bugs that are detectable from the code — including subtle, multi-bug, and
> non-local ones. Shared **intent** context (the task spec) changes the outcome
> only for the narrow class of bugs whose correctness is an arbitrary requirement
> absent from the code and from world knowledge. Shared **process** context (the
> coder's reasoning trace) transplants a blind spot **when it credibly reframes a
> bug as intended behavior** — the reviewer defers to a plausible "by design" claim
> — but not when the defense is checkably false. Shared **effort** buys nothing.

This decomposes Cognition's "zero shared context works best" into its parts:
*intent* helps narrowly, *process* hurts selectively (via credible "it's intended"
framing), *effort* is neutral — over a reviewer that is otherwise at ceiling. A
blanket "share nothing" heuristic lands in roughly the right place, but the two
halves that matter — share the intent, withhold the coder's rationalizations — pull
in opposite directions, which the blanket rule can't express.

This says *when* context matters and *why* — which the headline numbers could not.

## Honest limitations

- Small n (2–3 trials per cell); every claim is directional, and the raw run
  records are published so others can extend.
- The recall ceiling is a real ceiling: the contamination test and the
  effort/intent tests can only detect effects that would move recall *off* 100%.
- Seeded-bug recall is not natural-bug recall; the mix is stated, not hidden.
- The process-context result is two cases, n=5, with an author-defense trace
  elicitation; it demonstrates the mechanism but wants a larger sample to size it.

## Future work

- **Scale the process-context result.** More (buggy code, defending trace) pairs,
  and naturally-elicited traces from a weaker coder that genuinely errs, to size
  the blind-spot-transplant effect beyond the two cases shown here.
- **Find-then-verify.** A second agent that adversarially refutes each finding
  before it's reported — does a verify pass buy precision without costing recall?
- **Harder-to-judge frontier.** Bugs whose correctness requires computation the
  reviewer must actually perform, where even clean recall drops below 100%.

## Reproducing

Everything is config-plus-data. `python -m review_lab.runner --strict
[--task-spec] [--effort ...] --cases ...` runs any iteration over the evalset and
writes diffable JSONL run records plus an aggregate summary. The harness is the
artifact; the results table is the work sample.
