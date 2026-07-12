# Review Agent Lab

**Does giving a code-review agent more context make it better? A measured answer,
with the methodology Cognition's claim was missing.**

One custom review-agent harness (Opus 4.8, read-only tools, full-repo context),
run through controlled iterations against a 30-case seeded-bug evalset with strict,
audited scoring. Every claim below is backed by a committed, reproducible run.

## The headline

Cognition (April 2026) said a reviewer works best with **zero shared context**
with the coding agent — headline numbers, no published method. Decomposing that
one heuristic into its parts, each measured:

| Context you could share | Effect on the reviewer | Measured |
|---|---|---|
| **Intent** (the task spec) | **Helps — but only narrowly** | recall on arbitrary-rule bugs: **0% → 100%**; everything else already at ceiling |
| **Process** (the coder's reasoning trace) | **Hurts selectively** | when it credibly reframes a bug as *intended*, recall **100% → 60%** (controlled) — the reviewer defers to "it's by design" but refutes checkably-false claims |
| **Effort** (make it think harder) | **Neutral** | recall flat, **2.6× the cost** |

Underneath: a zero-context reviewer with repo access already catches ~**100%** of
bugs that are detectable in the diff — subtle, multi-bug, and non-local ones alike.
So context only changes outcomes at the margins.

**The precise rule:** *share the intent, never let the coder's "it's intended"
rationalizations reach the reviewer, and don't pay for more thinking — over a
reviewer that's otherwise at ceiling.*

## Read more

- **[WRITEUP.md](WRITEUP.md)** — the full narrative (motivation, rig, findings, limits)
- **[RESULTS.md](RESULTS.md)** — the numbers and tables
- **[INTERPRETATION.md](INTERPRETATION.md)** — plain-language reading + the Cognition verdict
- **[architecture.md](architecture.md)** — the original design

## How it works

A custom agent loop on the Anthropic Messages API (SDK tool runner), so context
assembly — the experiment variable — stays under byte-level control. The reviewer
gets a fixed, read-only tool set (`read_file`, `list_files`, `grep_repo`,
`get_diff`, and a single strict `report_finding`) over a **full source-tree
snapshot** of the repo at the commit. A two-stage scorer (deterministic location
match + an audited LLM judge, run in strict semantic mode) turns findings into
recall / precision / cost. Every case is tagged with training-contamination
provenance against the model's knowledge cutoff.

## Reproduce

```bash
uv venv && uv pip install -e .            # Python 3.12
# put ANTHROPIC_API_KEY in .env
python -m review_lab.run_once evalset/sample                     # one diff, end to end
python -m review_lab.runner --cases <ids> --strict [--task-spec] [--trace full] [--effort high]
```

Each run writes a diffable JSONL record plus an aggregate summary to `runs/`.
The harness is the artifact; the results table is the work sample.
