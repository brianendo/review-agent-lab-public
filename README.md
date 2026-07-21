# Review Agent Lab

[![tests + claim verification](https://github.com/brianendo/review-agent-lab-public/actions/workflows/test.yml/badge.svg)](https://github.com/brianendo/review-agent-lab-public/actions/workflows/test.yml)

**Does giving a code-review agent more context make it better? A measured answer,
with the methodology Cognition's claim was missing.**

One custom review-agent harness (Opus 4.8, read-only tools, full-repo context),
run through controlled iterations against a seeded-bug evalset (62 cases and
growing) with strict, audited scoring. Every claim below is backed by a
committed, reproducible run record in `runs/`.

> **This is the public subset of the lab.** 13 of the 62 cases are real diffs
> from private repositories; their source snapshots and run records are withheld
> here (49 cases ship in `evalset/`). Results tables that were measured on sets
> including those cases say so inline; the metrics-only run summaries in `runs/`
> cover every case, so the aggregate numbers still reconcile.

## The headline

Cognition (April 2026) said a reviewer works best with **zero shared context**
with the coding agent — headline numbers, no published method. Decomposing that
one heuristic into its parts, each measured:

| Context you could share | Effect on the reviewer | Measured |
|---|---|---|
| **Intent** (the task spec) | **Helps — but only narrowly** | recall on arbitrary-rule bugs: **0% → 100%**; everything else already at ceiling |
| **Process** (the coder's reasoning trace) | **Can only hurt — and only on judgment calls** | on objective bugs the trace's defenses are refuted every time (6/6 in the [committed replication](runs/panel-process-context/INDEX.md)); on spec-silent judgment calls the verdict is rig-unstable — original controlled test **100% → 60%**, replication 60% in *both* arms |
| **Effort** (make it think harder) | **Neutral** | recall flat, **2.6× the cost** |

Underneath: a zero-context reviewer with repo access already catches ~**100%** of
bugs that are detectable in the diff — subtle, multi-bug, and non-local ones alike.
So context only changes outcomes at the margins.

**The precise rule:** *share the intent, never let the coder's "it's intended"
rationalizations reach the reviewer, and don't pay for more thinking — over a
reviewer that's otherwise at ceiling.*

## The numbers, briefly

**Intent context moves exactly the arbitrary-rule bugs** (strict semantic
scoring; a catch must describe the seeded bug):

| case | the rule | diff only | + task spec |
|---|---|---|---|
| `intent-fee-floor` | fees floor to whole dollars | **0%** | **100%** |
| `intent-round-nickel` | round up to nearest nickel | **0%** | **100%** |
| `intent-retry-count` | exactly 5 attempts | **0%** | **100%** |
| `intent-grade-cutoff` | 93/85/77 cutoffs | **0%** | **100%** |
| `intent-tiebreak-id` | ties broken by ascending id | 100% | 100% |
| `intent-window-exclusive` | window end exclusive | 100% | 100% |
| `intent-tax-order` | discount before tax | 100% | 100% |

The four the reviewer misses blind are precisely the rules that live nowhere in
the code and nowhere in world knowledge. Rules that double as a general code
smell it catches unaided.

**More thinking buys nothing** (6-case subset, 2 trials/cell):

| effort | recall | cost per true positive |
|---|---|---|
| low | 100% | **$0.23** |
| medium | 100% | $0.45 |
| high | 100% | $0.60 |

**And the rest, one line each:**

- **Contamination control:** bugs merged *after* the model's cutoff are caught
  as reliably (100%) as famous old ones — the recall is capability, not memory.
- **False positives:** ~0.8 findings per clean diff over 5 no-bug diffs.
- **Model gradient:** appears only at multi-file scale with non-local root
  causes — on a 22-file mega-PR, Haiku 5/8 vs Opus 7/8; on single-function
  bugs, even Haiku is at ceiling.
- **Deception:** wrong comments plus passing-but-wrong tests fooled **no**
  model — reviewers re-derived the truth and said the tests were wrong.
- **Non-derivable bugs:** 15/15 caught across three models
  ([raw reports](runs/panel-nonderivable/INDEX.md)).

## Read more

- **[WRITEUP.md](WRITEUP.md)** — the full narrative (motivation, rig, findings, limits)
- **[RESULTS.md](RESULTS.md)** — the numbers and tables
- **[INTERPRETATION.md](INTERPRETATION.md)** — plain-language reading + the Cognition verdict
- **[evalset/NONDERIVABLE_RESULTS.md](evalset/NONDERIVABLE_RESULTS.md)** — the
  non-derivable battery (external invariants, cross-file contracts, TOCTOU): 15/15
  caught by a blind 3-model panel
- **[NOTICE.md](NOTICE.md)** — licenses and attribution for the OSS snapshots in
  the evalset

## Later batteries (after the writeup)

The evalset kept growing past the runs the writeup describes. Findings so far,
documented per-case in `evalset/*/manifest.json` and the commit log:

- **Scale doesn't break Opus.** A 6-file/10-bug PR, a ~16-file repo where the bug
  is a distant un-updated caller outside the diff, and a ~22-file repo with an
  8-file PR: Opus stays unbroken; a **model gradient** (Opus > Sonnet > Haiku)
  finally appears on the large feature PRs.
- **Deception fails.** A PR whose bugs are defended by confident comments *and*
  passing-but-wrong unit tests fools **no** model.
- **Non-derivable bugs fail to hide.** Bugs whose wrongness isn't in the diff text
  (at-least-once webhooks, AB-BA lock order, TOCTOU, enum desync, pagination
  contract): 15/15 caught across Opus/Sonnet/Haiku — see
  [NONDERIVABLE_RESULTS.md](evalset/NONDERIVABLE_RESULTS.md), replicated with
  the 15 raw blind-reviewer reports committed in
  [runs/panel-nonderivable/](runs/panel-nonderivable/INDEX.md).

## How it works

A custom agent loop on the Anthropic Messages API (SDK tool runner), so context
assembly — the experiment variable — stays under byte-level control. The reviewer
gets a fixed, read-only tool set (`read_file`, `list_files`, `grep_repo`,
`get_diff`, and a single strict `report_finding`) over a **full source-tree
snapshot** of the repo at the commit. A two-stage scorer (deterministic location
match + an audited LLM judge, run in strict semantic mode) turns findings into
recall / precision / cost. Every case is tagged with training-contamination
provenance against the model's knowledge cutoff.

## Verify the numbers without an API key

Every headline claim is recomputed from the committed run records on every CI
push. To check them yourself:

```bash
python tools/verify_results.py    # no key, no network — reads runs/ only
```

It re-derives the intent 0%→100% table case by case, the flat-recall/2.6×-cost
effort sweep, the pre- vs post-cutoff contamination control, the process-context
drop, and the clean-diff false-positive count, and fails if any published number
disagrees with the data. [EVALSET.md](EVALSET.md) catalogs all 49 cases
(regenerated from the manifests by `tools/gen_evalset_md.py`).

## Reproduce

```bash
uv venv && uv pip install -e .            # Python 3.11+
# put ANTHROPIC_API_KEY in .env
python -m review_lab.run_once evalset/sample                     # one diff, end to end
python -m review_lab.runner --cases <ids> --strict [--task-spec] [--trace full] [--effort high]
python -m review_lab.runner --help                               # all flags
```

Note: the runner makes real API calls; with no `--cases` filter it sweeps the
entire evalset (62 cases × 3 trials).

Each run writes a diffable JSONL record plus an aggregate summary to `runs/`.
The harness is the artifact; the results table is the work sample.
