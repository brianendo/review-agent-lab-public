"""Review one diff end to end and print + persist the result.

Usage:
    python -m review_lab.run_once [diff_dir]

diff_dir defaults to evalset/sample and must contain:
    diff.patch          the unified diff under review
    repo/               the repository the diff was applied to
    manifest.json       (optional) task_spec + seeded bugs, for eyeballing

Writes one JSONL run record to runs/ and prints the findings table.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Optional

from anthropic import Anthropic

from .harness import DEFAULT_MODEL, review_diff
from .scorer import cost_per_true_positive, score
from .tools import ReviewContext

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "runs"


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE lines from a .env file without overriding real env vars.

    Deliberately dependency-free and forgiving: blank lines and #comments are
    skipped, surrounding quotes are stripped, and anything already set in the
    environment wins (so an inline ANTHROPIC_API_KEY=... still takes precedence).
    """
    if not path.is_file():
        return
    for raw in path.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_case(diff_dir: Path):
    diff_text = (diff_dir / "diff.patch").read_text("utf-8")
    repo = diff_dir / "repo"
    manifest = {}
    manifest_path = diff_dir / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text("utf-8"))
    return diff_text, repo, manifest


def print_findings(result, manifest) -> None:
    print(f"\n{'=' * 72}")
    print(f"model={result.model}  thinking={result.thinking}  "
          f"turns={result.turns}  wall={result.wall_clock_s:.1f}s  "
          f"stop={result.stop_reason}")
    u = result.usage
    print(f"tokens: in={u.input_tokens} out={u.output_tokens} "
          f"cache_write={u.cache_creation_input_tokens} "
          f"cache_read={u.cache_read_input_tokens}")
    print(f"{'-' * 72}")
    if not result.findings:
        print("NO FINDINGS REPORTED")
    for i, f in enumerate(result.findings, 1):
        print(f"[{i}] {f.file}:{f.line}  severity={f.severity} confidence={f.confidence}")
        print(f"    {f.summary}")
        print(f"    scenario: {f.failure_scenario}")
    print(f"{'=' * 72}\n")


def print_score(result, sr) -> None:
    print(f"{'-' * 72}")
    rec = "n/a" if sr.recall is None else f"{sr.recall:.0%}"
    prec = "n/a" if sr.precision is None else f"{sr.precision:.0%}"
    print(f"SCORE  recall={rec} ({sr.n_caught}/{sr.n_bugs} bugs)  "
          f"precision={prec} ({sum(sr.finding_matched)}/{sr.n_findings} findings)  "
          f"judge_calls={sr.judge_calls}")
    u = result.usage
    cpt = cost_per_true_positive(
        u.input_tokens + u.cache_creation_input_tokens + u.cache_read_input_tokens,
        u.output_tokens, sr.n_caught)
    print(f"       cost/true-positive={'n/a' if cpt is None else f'${cpt:.4f}'}")
    for bm in sr.bug_matches:
        mark = "✓" if bm.caught else "✗"
        via = f" (via {bm.method})" if bm.caught else ""
        print(f"       {mark} {bm.bug_id}{via}")
    print(f"{'=' * 72}\n")


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m review_lab.run_once",
        description="Review one diff end to end (one API call chain, real spend) "
                    "and print + persist the result.")
    parser.add_argument("diff_dir", nargs="?", default="evalset/sample",
                        help="case directory containing diff.patch + repo/ "
                             "(default: evalset/sample)")
    parser.add_argument("--judge", action="store_true",
                        help="score findings with the LLM judge (extra API calls)")
    args = parser.parse_args(argv)

    diff_dir = Path(args.diff_dir)
    if not diff_dir.is_absolute():
        diff_dir = (REPO_ROOT / diff_dir).resolve()

    load_dotenv(REPO_ROOT / ".env")

    diff_text, repo, manifest = load_case(diff_dir)
    ctx = ReviewContext(repo_root=repo, diff_text=diff_text)

    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment (or .env)
    result = review_diff(
        client,
        ctx,
        model=DEFAULT_MODEL,
        task_spec=None,  # I0 baseline: diff only, no intent context
    )

    print_findings(result, manifest)

    bugs = manifest.get("bugs", [])
    sr = score(result.findings, bugs, client=client if args.judge else None,
               use_judge=args.judge)
    if bugs:
        print_score(result, sr)

    RUNS_DIR.mkdir(exist_ok=True)
    record = result.to_record()
    record["diff_id"] = manifest.get("diff_id", diff_dir.name)
    record["iteration"] = "I0-baseline"
    record["score"] = sr.to_dict() if bugs else None
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = RUNS_DIR / f"{record['diff_id']}-{stamp}.jsonl"
    out.write_text(json.dumps(record) + "\n", "utf-8")
    print(f"wrote run record: {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
