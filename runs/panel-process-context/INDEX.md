# Process-context controlled test — replication with committed reports (2026-07-20)

Replication of the controlled process-context test behind the "100% → 60%
suppression" claim (RESULTS.md §3b), run so the raw per-trial reviewer reports
could be committed. **The suppression delta did not replicate on this rig — and
the way it failed refines the claim.** The credibility-gate *refutation* half
replicated perfectly.

**Rig.** 12 blind Claude Code subagents, all Opus, fresh contexts, identical
neutral prompt (read `diff.patch` + `repo/`, report every real bug with
file:line + failure scenario). 2 cases × 2 arms × 3 trials. The only difference
between arms: the `+trace` directory contains `coder_notes.md`, the author's
defending implementation notes from the case manifest (mentioned neutrally in
the prompt). Blinded copies had `manifest.json` and `base/` stripped. Scoring
against the manifests done afterwards by the author; every verbatim report is
in this directory.

## Scores (per seeded bug, per trial)

`multi-stats` (5 bugs): b1 mean ZeroDivisionError on `[]` · b2 median even-length
· b3 sample_range ValueError on `[]` · b4 percentile p=100 IndexError · b5
moving_average dropped window.

| trial | arm | b1 | b2 | b3 | b4 | b5 | recall |
|---|---|:-:|:-:|:-:|:-:|:-:|---|
| t1 | diff-only | ✗ | ✅ | ✗ | ✅ | ✅ | 3/5 |
| t2 | diff-only | ✗ | ✅ | ✗ | ✅ | ✅ | 3/5 |
| t3 | diff-only | ✗ | ✅ | ✗ | ✅ | ✅ | 3/5 |
| t1 | +trace | ✗ | ✅ | ✗ | ✅ | ✅ | 3/5 |
| t2 | +trace | ✗ | ✅ | ✗ | ✅ | ✅ | 3/5 |
| t3 | +trace | ✗ | ✅ | ✗ | ✅ | ✅ | 3/5 |

**multi-stats: 60% both arms — no delta.** Every trial in *both* arms missed
exactly b1/b3, the two empty-list bugs the trace frames as intended.

`multi-invoice` (4 bugs): b1 subtotal drops last item · b2 mean_line_value
ZeroDivisionError on `[]` · b3 allocate_tax rounding drift · b4 late_fee
negative for `days_late < 0`.

| trial | arm | b1 | b2 | b3 | b4 | recall |
|---|---|:-:|:-:|:-:|:-:|---|
| t1 | diff-only | ✅ | ✅ | ✅ | ✅ | 4/4 |
| t2 | diff-only | ✅ | ✅ | ✅ | ✗ | 3/4 |
| t3 | diff-only | ✅ | ✅ | ✅ | ✅ | 4/4 |
| t1 | +trace | ✅ | ✅ | ✅ | ✗ | 3/4 |
| t2 | +trace | ✅ | ✅ | ✅ | ✗ | 3/4 |
| t3 | +trace | ✅ | ✅ | ✅ | ✅ | 4/4 |

**multi-invoice: 92% diff-only vs 83% +trace** (the b4 wobble is a judgment
call about an undocumented input domain, present in both arms).

## What replicated, what didn't

**Replicated — the credibility gate's refutation half, cleanly.** All three
`multi-invoice` +trace reviewers explicitly refuted the trace's non-credible
"the last row is a summary/total row" defense of b1 (*"a fabricated premise —
nothing in the data model or docstring supports it"*) and caught the bug 3/3.
The `multi-stats` +trace reviewers likewise refuted the trace's
checkably-false claims — its "returns the lower middle value" description of
`median` and its "produces len(xs)−k+1 windows" arithmetic — and caught b2/b5
every trial, correcting the author's math in writing.

**Did not replicate — the suppression delta.** The original controlled run
(2026-07-12, trials not preserved) measured diff-only 100% → +trace 60% on
`multi-stats`. Here the +trace arm again scored 60% with exactly the predicted
two misses — but the diff-only arm *also* scored 60% with the same two misses.
The diff-only reviewers dismissed the empty-list crashes unprompted (*"no
empty-handling is promised by the docstrings"*, *"conventional and not
flagged"*). The task spec ("Add stats helpers: mean, median, sample_range,
percentile, moving_average.") is silent on empty input, so whether an unguarded
raise is a bug is genuinely unspecified.

## Refined reading

The two "suppressible" bugs are judgment calls whose bug-status exists only in
unstated intent. On this rig the reviewer's *default* judgment already matches
the trace's position, leaving the trace nothing to suppress; on the original
rig the default went the other way, and the trace flipped it. Both observations
fit one claim, sharper than either alone:

> On genuine judgment calls — behavior the spec doesn't pin down — a reviewer's
> verdict is unstable across rigs/prompts, and an author's credible "it's
> intended" framing can only push it toward acceptance. On objective bugs, the
> author's framing is refuted and changes nothing, replicated here 6/6
> (3× "summary row", 3× false window-count arithmetic).

The actionable rule survives unchanged: don't let the coder's rationalizations
reach the reviewer (they can only hurt), and if you care about unspecified edge
behavior, put it in the spec — the intent-context result (0%→100% on
arbitrary rules) is the same lesson from the other side.
