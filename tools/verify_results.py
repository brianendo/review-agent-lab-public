"""Recompute the headline claims from the committed run records in runs/.

No API key, no network: this only reads the JSONL run records and metrics
summaries that every claim in README/RESULTS/PUBLIC_RESULTS cites. Run it to
check that the published numbers are what the committed data says.

    python tools/verify_results.py        # exits non-zero on any mismatch

Scope note: the controlled process-context test (multi-stats 100% -> 60%) and
the model-panel batteries ran on a blind-subagent rig; their evidence is the
committed reviewer reports, not harness JSONL, so they are referenced but not
recomputed here.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(label)


def load_summary(prefix: str) -> dict:
    paths = sorted(RUNS.glob(f"{prefix}-2*.summary.json"))
    if not paths:
        sys.exit(f"missing run summary: runs/{prefix}-*.summary.json")
    return json.loads(paths[-1].read_text())


def per_diff_recall(summary: dict) -> dict:
    return {k: v["recall_mean"] for k, v in summary["per_diff"].items()
            if v.get("recall_mean") is not None}


print("== 1. Intent context helps only for arbitrary rules "
      "(intent-I0/I2a + v-intent-I0/I2a) ==")
i0 = {**per_diff_recall(load_summary("intent-I0")),
      **per_diff_recall(load_summary("v-intent-I0"))}
i2a = {**per_diff_recall(load_summary("intent-I2a")),
       **per_diff_recall(load_summary("v-intent-I2a"))}
ARBITRARY = ["intent-fee-floor", "intent-round-nickel", "intent-retry-count",
             "intent-grade-cutoff"]
SMELL = ["intent-tiebreak-id", "intent-window-exclusive", "intent-tax-order"]
for case in ARBITRARY:
    check(f"{case}: 0% without spec -> 100% with spec",
          i0[case] == 0.0 and i2a[case] == 1.0,
          f"I0={i0[case]:.0%} I2a={i2a[case]:.0%}")
for case in SMELL:
    check(f"{case}: already 100% without spec",
          i0[case] == 1.0 and i2a[case] == 1.0,
          f"I0={i0[case]:.0%} I2a={i2a[case]:.0%}")
mean_i0 = sum(i0[c] for c in ARBITRARY + SMELL) / 7
check("7-case mean 43% -> 100%",
      round(mean_i0, 2) == 0.43 and all(i2a[c] == 1.0 for c in ARBITRARY + SMELL),
      f"I0 mean={mean_i0:.0%}")

print("== 2. Effort is neutral; cost is not (I1 sweep, 6-case subset) ==")
efforts = {e: load_summary(f"I1-{e}") for e in ("low", "medium", "high")}
for e, s in efforts.items():
    check(f"effort={e}: recall pinned at 100%",
          s["overall"]["micro_recall"] == 1.0)
lo = efforts["low"]["overall"]["cost_per_true_positive"]
hi = efforts["high"]["overall"]["cost_per_true_positive"]
check("cost per true positive rises ~2.6x low -> high",
      2.3 <= hi / lo <= 2.9, f"${lo:.3f} -> ${hi:.3f} = {hi / lo:.2f}x")

print("== 3. Contamination control: pre- vs post-cutoff, no gap "
      "(contamination-I0) ==")
cont = per_diff_recall(load_summary("contamination-I0"))
PRE = ["httpx-cancel-close", "requests-scheme"]
POST = ["anyio-capacitylimiter-inf", "pydantic-falsy-alias"]
for case in PRE + POST:
    tag = "pre-cutoff (memorizable)" if case in PRE else "post-cutoff (unseen)"
    check(f"{case} [{tag}]: 100%", cont[case] == 1.0, f"{cont[case]:.0%}")

print("== 4. Process context, two-rig pooled pass (I2b2; the controlled "
      "subagent test sharpened this to 100%->60%) ==")
d = load_summary("I2b2-diffonly")["overall"]["micro_recall"]
t = load_summary("I2b2-trace")["overall"]["micro_recall"]
check("pooled recall 82% diff-only -> 74% with coder trace",
      round(d, 2) == 0.82 and round(t, 2) == 0.74, f"{d:.0%} -> {t:.0%}")

print("== 5. False-positive rate on clean public diffs (PUB-I0 records) ==")
CLEAN = {"clean-slugify", "clean-units", "clean-click-zfs",
         "clean-rich-expandable", "clean-rich-linkids"}
findings = {c: 0 for c in CLEAN}
seen = set()
for path in sorted(RUNS.glob("PUB-I0-2*.jsonl")):
    for line in path.read_text().splitlines():
        rec = json.loads(line)
        if rec["diff_id"] in CLEAN:
            findings[rec["diff_id"]] += len(rec.get("findings", []))
            seen.add(rec["diff_id"])
total = sum(findings.values())
check("5 clean diffs, 4 findings total (~0.8/diff)",
      seen == CLEAN and total == 4,
      f"{total} findings over {len(seen)} clean diffs")

print()
if failures:
    print(f"{len(failures)} CLAIM(S) DO NOT MATCH THE COMMITTED DATA:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("All published claims match the committed run records.")
