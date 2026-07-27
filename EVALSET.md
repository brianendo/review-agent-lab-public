# Evalset catalog

49 cases, generated from each case's `manifest.json` (`python tools/gen_evalset_md.py .` regenerates this file). `cutoff` is the case's position relative to the reviewer model's Jan-2026 training cutoff: `post` = merged after (contamination-clean), `pre` = contamination control, `na` = synthetic/private (never public).

| case | source | cutoff | bugs | what it tests |
|---|---|---|---|---|
| `anyio-capacitylimiter-inf` | public-oss | post | 1 | public repo, fix merged 2026-06-27 after the 2026-01-31 model cutoff; post-cutoff, contamination-clean. |
| `bigpr-order-pipeline` | synthetic-bigpr | na | 10 | 6-file, 10-bug dense PR with deep non-local root causes; built to stress even Opus (recall as fraction, coverage limit) |
| `bigrepo-proration` | synthetic-bigrepo | na | 1 | ~16-file repo; the bug is a distant un-updated caller (renewal.py) NOT in the diff, so catching it requires navigating the repo to find all callers of the changed function. Tests repo-scale navigation, not inline review. |
| `clean-click-zfs` | public-oss-clean | post | 0 | real OSS change merged 2026-05-28 (post-cutoff), presumed correct; measures false-positive rate |
| `clean-rich-expandable` | public-oss-clean | post | 0 | real OSS change merged 2026-04-11 (post-cutoff), presumed correct; measures false-positive rate |
| `clean-rich-linkids` | public-oss-clean | post | 0 | real OSS change merged 2026-02-26 (post-cutoff), presumed correct; measures false-positive rate |
| `clean-slugify` | synthetic-clean | na | 0 | correct code, no seeded bug; measures false-positive rate |
| `clean-units` | synthetic-clean | na | 0 | correct code, no seeded bug; measures false-positive rate |
| `click-choice-brackets` | public-oss | post | 1 | public repo, fix merged 2026-06-12 after the 2026-01-31 model cutoff; post-cutoff, contamination-clean. |
| `deception-tests` | synthetic-deception | na | 3 | DECEPTION: each bug contradicts the stated spec but is defended by a confident comment AND a passing-but-wrong unit test that asserts the buggy output. Tests whether green tests + plausible comments make the reviewer defer (credibility gate). A caught bug = flagging code contradicts spec despite the test. |
| `ext-pagination` | synthetic-nonderivable | na | 1 | EXTERNAL API CONTRACT: 'short page == last page' is a wrong assumption about cursor pagination; correct termination is next_cursor is None. Not derivable from the code. |
| `ext-webhook-idem` | synthetic-nonderivable | na | 1 | EXTERNAL-INVARIANT: code is locally correct; the bug (missing idempotency) is only wrong because payment webhooks are at-least-once and retried. Not derivable from the diff -- requires external domain knowledge. |
| `featurepr-promo-codes` | synthetic-featurepr | na | 5 | large multi-file feature PR: 5 graded bugs (2 non-local) + unspecified points; tests scale + ambiguity |
| `hard-business-days` | synthetic-hard | na | 1 | subtle bug requiring reasoning/domain knowledge to catch |
| `hard-cache-key` | synthetic-hard | na | 1 | cache keyed on subset of inputs; subtle state bug |
| `hard-cache-stale` | synthetic-hard | na | 1 | freshly authored, calibrated to be hard to JUDGE (bug is locally plausible) |
| `hard-compound-interest` | synthetic-hard | na | 1 | subtle bug requiring reasoning/domain knowledge to catch |
| `hard-discount-tacit` | synthetic-hard | na | 1 | freshly authored, calibrated to be hard to JUDGE (bug is locally plausible) |
| `hard-ledger-holds` | synthetic-hard | na | 1 | bespoke stateful interaction bug; no textbook pattern, no worked example |
| `hard-lower-bound` | synthetic-hard | na | 1 | subtle bug requiring reasoning/domain knowledge to catch |
| `hard-lru-refresh` | synthetic-hard | na | 1 | bespoke stateful interaction bug; no textbook pattern, no worked example |
| `hard-mutable-default` | synthetic-hard | na | 1 | classic mutable-default-arg bug; subtle but first-principles |
| `hard-orderbook-sorted` | synthetic-hard | na | 1 | freshly authored, calibrated to be hard to JUDGE (bug is locally plausible) |
| `hard-parser-quotes` | synthetic-hard | na | 1 | bespoke stateful interaction bug; no textbook pattern, no worked example |
| `hard-percentile-interp` | synthetic-hard | na | 1 | subtle bug requiring reasoning/domain knowledge to catch |
| `hard-rate-limiter` | synthetic-hard | na | 1 | subtle bug requiring reasoning/domain knowledge to catch |
| `httpx-cancel-close` | public-oss | pre | 1 | public repo, PR merged before the Jan-2026 model cutoff; likely memorized. Treat as a contamination control, exclude from headline recall. |
| `intent-batch-size` | synthetic-intent | na | 1 | arbitrary batch-size limit; only in spec |
| `intent-fee-floor` | synthetic | na | 1 | freshly authored for this evalset |
| `intent-grade-cutoff` | synthetic-intent | na | 1 | arbitrary grade cutoffs; only in spec |
| `intent-id-pad` | synthetic-intent | na | 1 | arbitrary ID format; only in spec |
| `intent-retry-count` | synthetic-arbitrary | na | 1 | arbitrary rule lives ONLY in task_spec; not derivable from code or world knowledge |
| `intent-round-nickel` | synthetic-arbitrary | na | 1 | arbitrary rule lives ONLY in task_spec; not derivable from code or world knowledge |
| `intent-tax-order` | synthetic-intent | na | 1 | arbitrary order-of-operations rule; only in spec |
| `intent-tiebreak-id` | synthetic-arbitrary | na | 1 | arbitrary rule lives ONLY in task_spec; not derivable from code or world knowledge |
| `intent-window-exclusive` | synthetic-arbitrary | na | 1 | arbitrary rule lives ONLY in task_spec; not derivable from code or world knowledge |
| `megapr-fulfillment` | synthetic-megapr | na | 8 | ~22-file repo, 8-file complex PR, 9 graded bugs incl deep non-local (allocate non-conservation, signature break of distant caller checkout.py, free-ship interaction, refund-sign break consumed by jobs/reconcile.py). Requires navigation; tests coverage limit at high complexity. |
| `multi-geometry` | synthetic-multi | na | 4 | 5-function geometry module, graded bugs; I2b process-context case |
| `multi-invoice` | synthetic-multi | na | 4 | 5 graded-subtlety bugs in one diff to measure fractional recall |
| `multi-parse` | synthetic-multi | na | 4 | 5-function config module, graded bugs; I2b process-context case |
| `multi-stats` | synthetic-multi | na | 5 | 5 graded bugs; second I2b process-context case |
| `pydantic-falsy-alias` | public-oss | post | 1 | public repo, fix merged 2026-06-01 after the 2026-01-31 model cutoff; post-cutoff, contamination-clean. |
| `requests-scheme` | public-oss | pre | 1 | public repo, PR merged before the Jan-2026 model cutoff; likely memorized. Treat as a contamination control, exclude from headline recall. |
| `rich-ansi-newlines` | public-oss | post | 1 | public repo, fix merged 2026-04-12 after the 2026-01-31 model cutoff; post-cutoff, contamination-clean. |
| `sample` | synthetic | na | 1 | freshly authored for this evalset |
| `subtle-bsearch` | synthetic-multi | na | 1 | subtle algorithmic infinite-loop bug; hard to verify without simulating |
| `toctou-reserve` | synthetic-nonderivable | na | 1 | TOCTOU: the check-then-act gap is only a bug under concurrent interleaving; a single-threaded read of the function looks correct. Requires imagining the race. |
| `xfile-enum-desync` | synthetic-nonderivable | na | 1 | CROSS-FILE DESYNC: the new enum case has no branch in the dispatch table in another file, silently taking a wrong default. The stale table is OUTSIDE the diff. |
| `xfile-lock-order` | synthetic-nonderivable | na | 1 | CROSS-FILE INVARIANT: each function is locally correct; the deadlock exists only in the RELATIONSHIP between two files' lock-acquisition orders. No stated contract. |
