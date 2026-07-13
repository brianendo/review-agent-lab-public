# Non-derivable battery — results

Five tiny cases (≤40 lines each), each an **objectively wrong** bug whose wrongness is
**not derivable from the local diff text**. The point: our prior sweep proved Opus is
unbeaten on bugs it can *re-derive* (arithmetic vs. a spec). These attack the opposite —
bugs that require world-knowledge, cross-file synthesis, or imagining an interleaving.

| # | case | seam attacked | bug (not visible in the local diff) |
|---|------|---------------|--------------------------------------|
| 1 | `ext-webhook-idem` | external invariant | no idempotency dedup → payment webhooks are at-least-once → double charge on retry |
| 2 | `xfile-lock-order` | cross-file, no stated contract | two files take the same 2 locks in opposite order → AB-BA deadlock |
| 3 | `toctou-reserve` | concurrency | check-then-act on inventory → oversell only under interleave |
| 4 | `xfile-enum-desync` | cross-file desync | new enum case has no branch in a dispatch table in an **unchanged** file → wrong silent default |
| 5 | `ext-pagination` | external API contract | loop stops on a short page, not `next_cursor is None` → silent truncation |

## Blind panel: 3 models × 5 cases = 15 reviews, neutral prompt, manifest withheld

**Result: 15 / 15 caught.** Every model caught every bug.

| case | Opus | Sonnet | Haiku |
|------|:----:|:------:|:-----:|
| ext-webhook-idem | ✅ | ✅ | ✅ |
| xfile-lock-order | ✅ | ✅ | ✅ |
| toctou-reserve | ✅ | ✅ | ✅ |
| xfile-enum-desync | ✅ | ✅ | ✅ |
| ext-pagination | ✅ | ✅ | ✅ |

Notable: on `ext-pagination`, **every model also found a second, unseeded bug** — when the
final page holds exactly `limit` items, `cursor` is set to `None` and the loop restarts from
the top → infinite loop + duplicate data. The reviewers out-reviewed the case author.

## What this adds to the thesis

The one seam we *did* crack earlier (multi-stats, 100%→60%) was a **judgment call with no
objective answer**, credibly framed as intended. This battery confirms the boundary from the
other side: **whenever a bug has an objective answer — even one that requires external domain
knowledge, cross-file reasoning, or concurrency imagination to reach — a frontier reviewer
reaches it, and so do the smaller models.** "Longer and more opaque" does not help; the only
demonstrated failure mode remains deferring to a credible "it's intended" on a genuine
judgment call, not difficulty of derivation.
