# Non-derivable battery — blind panel re-run, 2026-07-20 (raw reports)

Independent replication of the 15/15 result in
[`evalset/NONDERIVABLE_RESULTS.md`](../../evalset/NONDERIVABLE_RESULTS.md),
run so the raw reviewer reports could be committed as evidence.

**Rig.** 15 blind Claude Code subagents (5 cases × Haiku 4.5 / Sonnet /
Opus 4.8), each with a fresh context and an identical neutral prompt: read
`diff.patch` and the `repo/` snapshot, report every real bug with file:line,
summary, and a concrete failure scenario. Reviewers were given a copy of the
case with `manifest.json` and `base/` removed, so the seeded bug and its
description were unavailable to them. One trial per cell. Each report in this
directory is the reviewer's verbatim final message; scoring against the
manifests was done afterwards by the author.

**Result: 15/15 — every model caught every seeded bug. Replicates the
original panel exactly.**

| case | seeded bug (not derivable from the local diff) | Haiku | Sonnet | Opus |
|---|---|:-:|:-:|:-:|
| `ext-webhook-idem` | missing idempotency vs at-least-once webhooks → double charge | ✅ | ✅ | ✅ |
| `xfile-lock-order` | AB-BA lock order across two files → deadlock | ✅ | ✅ | ✅ |
| `toctou-reserve` | check-then-act inventory race → oversell | ✅ | ✅ | ✅ |
| `xfile-enum-desync` | new enum case missing from dispatch table in an unchanged file | ✅ | ✅ | ✅ |
| `ext-pagination` | terminates on short page instead of `next_cursor is None` | ✅ | ✅ | ✅ |

Notable, replicating the original run: on `ext-pagination`, all three models
also independently derived the unseeded second failure mode (final page exactly
`limit` items → `cursor = None` → pagination restarts from the top → infinite
loop + duplicates). Several reviewers reported additional plausible unseeded
findings (e.g. missing `qty <= 0` validation in `toctou-reserve`, unpersisted
status write and unverified payload in `ext-webhook-idem`, an unreachable-code
`NameError` in `xfile-enum-desync`); these are not scored here — recall is
against the seeded bug only.

Caveat: this rig is Claude Code subagents with read tools, not the
byte-controlled harness (`src/review_lab/`); it demonstrates the same
result on the same cases with the model unable to see the answer key.
