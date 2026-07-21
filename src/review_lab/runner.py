"""Run one iteration (a config) over the evalset, N trials per diff, concurrently.

    python -m review_lab.runner [--trials N] [--workers K] [--judge]
                                [--cases a,b,c] [--iteration I0-baseline]

An iteration = one Config run over every case, `trials` times each. Each run is
independent (its own ReviewContext + tools), so we fan out over a thread pool;
the Anthropic client is shared and thread-safe. Every run appends a JSONL record
(run id, iteration, config hash, diff id, trial, findings, usage, wall, score) to
runs/<iteration>-<...>.jsonl, and the aggregate table is printed and saved.

This is the rig from architecture.md: results from any two iterations compose
into one comparison table because the evalset, scorer, and record schema are fixed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from .harness import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, review_diff
from .run_once import REPO_ROOT, RUNS_DIR, load_case, load_dotenv
from .scorer import cost_per_true_positive, score

EVALSET = REPO_ROOT / "evalset"
TRACE_CHAR_CAP = 8000  # ~2k tokens: fixed cap so trace length is not a confound

# Effort levels for the I1 sweep -> (output_config.effort value, max_tokens).
# Opus 4.8 uses adaptive thinking + output_config.effort; higher effort also
# gets a higher output ceiling so long reasoning has room.
EFFORT = {
    "low":    ("low", DEFAULT_MAX_TOKENS),
    "medium": ("medium", 12000),
    "high":   ("high", 16000),
    "xhigh":  ("xhigh", 24000),
}


@dataclass
class Config:
    """One iteration's knobs. Everything that changes the reviewer lives here."""

    iteration: str = "I0-baseline"
    model: str = DEFAULT_MODEL
    thinking: Optional[str] = "adaptive"
    effort: Optional[str] = None  # I1 sweep: overrides thinking+max_tokens via EFFORT
    max_iterations: int = 30
    cache_prefix: bool = True
    use_task_spec: bool = False  # I2a flips this on
    trace_mode: Optional[str] = None  # I2b: "full" or "summary" (from manifest)

    def config_hash(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:12]


@dataclass
class Cell:
    diff_id: str
    trial: int
    n_bugs: int
    n_findings: int
    n_caught: int
    recall: Optional[float]
    precision: Optional[float]
    input_tokens: int
    output_tokens: int
    cache_read: int
    cache_write: int
    wall_s: float
    error: Optional[str] = None


def discover_cases(only: Optional[List[str]] = None) -> List[Path]:
    cases = []
    for d in sorted(EVALSET.iterdir()):
        if (d / "manifest.json").is_file() and (d / "diff.patch").is_file() and (d / "repo").is_dir():
            if only is None or d.name in only:
                cases.append(d)
    return cases


def run_cell(client: Anthropic, case_dir: Path, config: Config, trial: int,
             use_judge: bool, strict: bool = False) -> Cell:
    diff_text, repo, manifest = load_case(case_dir)
    bugs = manifest.get("bugs", [])
    task_spec = manifest.get("task_spec") if config.use_task_spec else None
    trace = None
    if config.trace_mode == "full":
        trace = manifest.get("coder_trace")
    elif config.trace_mode == "summary":
        trace = manifest.get("coder_trace_summary")
    if trace:
        trace = trace[:TRACE_CHAR_CAP]  # fixed cap so trace length is not a confound
    from .tools import ReviewContext
    ctx = ReviewContext(repo_root=repo, diff_text=diff_text)
    effort_val, max_tokens = (EFFORT[config.effort] if config.effort
                              else (None, DEFAULT_MAX_TOKENS))
    try:
        result = review_diff(
            client, ctx, model=config.model, task_spec=task_spec, trace=trace,
            max_iterations=config.max_iterations, thinking=config.thinking,
            effort=effort_val, max_tokens=max_tokens, cache_prefix=config.cache_prefix,
        )
        needs_judge = use_judge or strict
        sr = score(result.findings, bugs,
                   client=client if needs_judge else None, use_judge=use_judge,
                   require_semantic_match=strict)
        u = result.usage
        cell = Cell(
            diff_id=manifest.get("diff_id", case_dir.name), trial=trial,
            n_bugs=sr.n_bugs, n_findings=sr.n_findings, n_caught=sr.n_caught,
            recall=sr.recall, precision=sr.precision,
            input_tokens=u.input_tokens, output_tokens=u.output_tokens,
            cache_read=u.cache_read_input_tokens, cache_write=u.cache_creation_input_tokens,
            wall_s=round(result.wall_clock_s, 2),
        )
        # Persist the full run record (findings included) for later re-scoring.
        record = result.to_record()
        record.update({"iteration": config.iteration, "config_hash": config.config_hash(),
                       "diff_id": cell.diff_id, "trial": trial, "score": sr.to_dict()})
        return cell, record
    except Exception as exc:  # a dead run should not kill the sweep
        return Cell(diff_id=case_dir.name, trial=trial, n_bugs=len(bugs),
                    n_findings=0, n_caught=0, recall=None, precision=None,
                    input_tokens=0, output_tokens=0, cache_read=0, cache_write=0,
                    wall_s=0.0, error=f"{type(exc).__name__}: {exc}"), None


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None


def _std(xs):
    xs = [x for x in xs if x is not None]
    return statistics.pstdev(xs) if len(xs) > 1 else 0.0


def aggregate_and_print(cells: List[Cell], config: Config) -> Dict[str, Any]:
    by_diff: Dict[str, List[Cell]] = {}
    for c in cells:
        by_diff.setdefault(c.diff_id, []).append(c)

    print(f"\n{'=' * 78}")
    print(f"ITERATION {config.iteration}  (config {config.config_hash()}, "
          f"model={config.model}, thinking={config.thinking}, task_spec={config.use_task_spec})")
    print(f"{'=' * 78}")
    print(f"{'diff':<22}{'trials':>7}{'recall':>10}{'precision':>11}{'$/run':>9}{'errors':>8}")
    print(f"{'-' * 78}")

    per_diff = {}
    total_caught = total_bugs = total_in = total_out = 0
    all_recall, all_prec = [], []
    for diff_id, cs in sorted(by_diff.items()):
        ok = [c for c in cs if c.error is None]
        errs = len(cs) - len(ok)
        rec = _mean([c.recall for c in ok])
        prec = _mean([c.precision for c in ok])
        cost = _mean([cost_per_true_positive(c.input_tokens + c.cache_read + c.cache_write,
                                             c.output_tokens, 1) for c in ok])  # $/run
        rec_s = "n/a" if rec is None else f"{rec:.0%}±{_std([c.recall for c in ok]):.0%}"
        prec_s = "n/a" if prec is None else f"{prec:.0%}"
        print(f"{diff_id:<22}{len(cs):>7}{rec_s:>10}{prec_s:>11}"
              f"{('$'+format(cost,'.3f')) if cost else 'n/a':>9}{errs:>8}")
        per_diff[diff_id] = {"trials": len(cs), "recall_mean": rec, "precision_mean": prec,
                             "recall_std": _std([c.recall for c in ok]), "errors": errs}
        for c in ok:
            total_caught += c.n_caught
            total_bugs += c.n_bugs
            total_in += c.input_tokens + c.cache_read + c.cache_write
            total_out += c.output_tokens
            if c.recall is not None:
                all_recall.append(c.recall)
            if c.precision is not None:
                all_prec.append(c.precision)

    overall_recall = (total_caught / total_bugs) if total_bugs else None
    cpt = cost_per_true_positive(total_in, total_out, total_caught)
    print(f"{'-' * 78}")
    print(f"OVERALL  micro-recall={overall_recall:.0%} ({total_caught}/{total_bugs} bugs)  "
          f"macro-precision={_mean(all_prec):.0%}  " if overall_recall is not None else "OVERALL  ")
    print(f"         cost/true-positive={'n/a' if cpt is None else f'${cpt:.4f}'}  "
          f"total spend=${(total_in*5 + total_out*25)/1e6:.2f}")
    print(f"{'=' * 78}\n")

    return {
        "iteration": config.iteration, "config": asdict(config),
        "config_hash": config.config_hash(),
        "overall": {"micro_recall": overall_recall, "macro_precision": _mean(all_prec),
                    "cost_per_true_positive": cpt, "total_bugs": total_bugs,
                    "total_caught": total_caught},
        "per_diff": per_diff,
    }


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m review_lab.runner",
        description="Run one iteration (a config) over the evalset, N trials per "
                    "case, concurrently. Every cell is a real API call chain — "
                    "the default invocation sweeps the whole evalset with spend.")
    parser.add_argument("--trials", type=int, default=3,
                        help="trials per case (default: 3)")
    parser.add_argument("--workers", type=int, default=3,
                        help="concurrent runs (default: 3)")
    parser.add_argument("--judge", action="store_true",
                        help="score findings with the LLM judge")
    parser.add_argument("--strict", action="store_true",
                        help="strict semantic scoring: a catch must describe the "
                             "seeded bug, not just hit its location")
    parser.add_argument("--cases", metavar="a,b,c",
                        help="comma-separated case ids (default: all of evalset/)")
    parser.add_argument("--iteration", default="I0-baseline",
                        help="iteration label for the run record (default: I0-baseline)")
    parser.add_argument("--effort", choices=list(EFFORT),
                        help="I1 sweep: override thinking effort")
    parser.add_argument("--trace", choices=["full", "summary"],
                        help="I2b: attach the coder's trace from the manifest")
    parser.add_argument("--task-spec", action="store_true",
                        help="I2a: attach the task spec (intent context)")
    args = parser.parse_args(argv)

    trials = args.trials
    workers = args.workers
    use_judge = args.judge
    strict = args.strict
    only = args.cases.split(",") if args.cases else None
    config = Config(iteration=args.iteration, use_task_spec=args.task_spec,
                    effort=args.effort, trace_mode=args.trace)

    load_dotenv(REPO_ROOT / ".env")
    client = Anthropic()
    cases = discover_cases(only)
    if not cases:
        print("no cases found in evalset/")
        return 1
    print(f"running {config.iteration}: {len(cases)} cases x {trials} trials "
          f"= {len(cases) * trials} runs, {workers} workers")

    cells: List[Cell] = []
    records: List[dict] = []
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(run_cell, client, case, config, t, use_judge, strict): (case.name, t)
                for case in cases for t in range(1, trials + 1)}
        done = 0
        for fut in as_completed(futs):
            cell, record = fut.result()
            cells.append(cell)
            if record:
                records.append(record)
            done += 1
            name, t = futs[fut]
            status = cell.error if cell.error else f"recall={'n/a' if cell.recall is None else format(cell.recall,'.0%')}"
            print(f"  [{done}/{len(futs)}] {name} trial {t}: {status}")
    wall = time.monotonic() - start

    summary = aggregate_and_print(cells, config)
    summary["wall_s"] = round(wall, 1)

    RUNS_DIR.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    runs_path = RUNS_DIR / f"{config.iteration}-{stamp}.jsonl"
    with runs_path.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    (RUNS_DIR / f"{config.iteration}-{stamp}.summary.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    print(f"wrote {len(records)} run records -> {runs_path.relative_to(REPO_ROOT)}")
    print(f"wrote summary -> {runs_path.stem}.summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
