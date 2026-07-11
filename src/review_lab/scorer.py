"""Score reviewer findings against a diff's seeded ground truth.

Two-stage matching (architecture.md):

  1. Location match  -- deterministic: same file, finding line within the bug's
     line range widened by DRIFT lines. Catches most cases with no API cost.
  2. LLM judge fallback -- for near misses (a finding in the right file that no
     bug location-matched), one judge call decides "is this finding describing
     this seeded bug?" via structured output. The judge sees only the bug
     description and the finding -- never which iteration or config produced it.

From the matches we report the four numbers every iteration shares:
  recall     = seeded bugs caught / seeded bugs present
  precision  = findings matching a seed / total findings
  (cost per true positive is an aggregate over a run's token usage; see
   cost_per_true_positive(), fed by the runner's accounting.)

A finding matches at most one bug and a bug is caught by at most one finding, so
counts never double-count. Multiple findings can each be false positives.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel, Field

from .tools import Finding

DRIFT = 5  # lines of tolerance for location match, per architecture.md
DEFAULT_JUDGE_MODEL = "claude-sonnet-5"


class JudgeVerdict(BaseModel):
    """Structured judge output for the near-miss fallback."""

    matches: bool = Field(description="True iff the finding describes this seeded bug.")
    reasoning: str = Field(description="One sentence justifying the verdict.")


@dataclass
class BugMatch:
    bug_id: str
    caught: bool
    method: Optional[str]  # "location" | "judge" | None
    finding_index: Optional[int]


@dataclass
class ScoreResult:
    bug_matches: List[BugMatch]
    finding_matched: List[bool]  # parallel to the findings list
    n_bugs: int
    n_findings: int
    n_caught: int
    recall: Optional[float]      # None when there are no seeded bugs (clean diff)
    precision: Optional[float]   # None when the reviewer reported nothing
    judge_calls: int = 0
    judge_usage: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


def _location_match(finding: Finding, bug: Dict[str, Any]) -> bool:
    lines = bug.get("lines") or []
    if not lines or finding.file != bug["file"]:
        return False
    lo, hi = min(lines) - DRIFT, max(lines) + DRIFT
    return lo <= finding.line <= hi


def _judge(client, model: str, bug: Dict[str, Any], finding: Finding) -> tuple[bool, Any]:
    """Ask the judge whether `finding` describes `bug`. Returns (matches, usage)."""
    prompt = (
        "You are grading a code review. Decide whether the reviewer's FINDING is "
        "describing the same underlying bug as the SEEDED BUG. Same root cause and "
        "location counts as a match even if wording or exact line differs. A finding "
        "about a different defect does not.\n\n"
        f"SEEDED BUG:\n"
        f"  file: {bug['file']}\n"
        f"  lines: {bug.get('lines')}\n"
        f"  category: {bug.get('category')}\n"
        f"  description: {bug.get('description')}\n\n"
        f"REVIEWER FINDING:\n"
        f"  file: {finding.file}\n"
        f"  line: {finding.line}\n"
        f"  summary: {finding.summary}\n"
        f"  failure_scenario: {finding.failure_scenario}\n"
    )
    resp = client.messages.parse(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
        output_format=JudgeVerdict,
    )
    verdict = resp.parsed_output
    return (bool(verdict and verdict.matches), resp.usage)


def score(
    findings: Sequence[Finding],
    bugs: Sequence[Dict[str, Any]],
    *,
    client=None,
    judge_model: str = DEFAULT_JUDGE_MODEL,
    use_judge: bool = True,
    require_semantic_match: bool = False,
) -> ScoreResult:
    """Score findings against seeded bugs.

    The judge fallback runs only when `use_judge` and a `client` are given; with
    no client, scoring is purely deterministic (location match only).

    require_semantic_match (needs a client) makes a location hit count as a catch
    ONLY if the judge confirms the finding actually describes that bug. Without
    it, any finding on the right line is credited -- which over-counts for intent
    bugs, where a finding can hit the right line for the wrong reason.
    """
    finding_matched = [False] * len(findings)
    bug_matches: List[BugMatch] = []
    judge_calls = 0
    judge_usage = {"input_tokens": 0, "output_tokens": 0}
    semantic = require_semantic_match and client is not None

    # Stage 1: location match (optionally semantically confirmed by the judge).
    for bug in bugs:
        hit_idx: Optional[int] = None
        for i, f in enumerate(findings):
            if finding_matched[i] or not _location_match(f, bug):
                continue
            if semantic:
                judge_calls += 1
                ok, usage = _judge(client, judge_model, bug, f)
                judge_usage["input_tokens"] += getattr(usage, "input_tokens", 0) or 0
                judge_usage["output_tokens"] += getattr(usage, "output_tokens", 0) or 0
                if not ok:
                    continue  # right line, wrong bug -> keep looking
            hit_idx = i
            break
        if hit_idx is not None:
            finding_matched[hit_idx] = True
            method = "location+judge" if semantic else "location"
            bug_matches.append(BugMatch(bug["bug_id"], True, method, hit_idx))
        else:
            bug_matches.append(BugMatch(bug["bug_id"], False, None, None))

    # Stage 2: judge fallback for still-uncaught bugs, over same-file findings
    # that haven't already been claimed by another bug.
    if use_judge and client is not None:
        for bm, bug in zip(bug_matches, bugs):
            if bm.caught:
                continue
            for i, f in enumerate(findings):
                if finding_matched[i] or f.file != bug["file"]:
                    continue
                judge_calls += 1
                matched, usage = _judge(client, judge_model, bug, f)
                judge_usage["input_tokens"] += getattr(usage, "input_tokens", 0) or 0
                judge_usage["output_tokens"] += getattr(usage, "output_tokens", 0) or 0
                if matched:
                    finding_matched[i] = True
                    bm.caught, bm.method, bm.finding_index = True, "judge", i
                    break

    n_caught = sum(1 for bm in bug_matches if bm.caught)
    recall = (n_caught / len(bugs)) if bugs else None
    precision = (sum(finding_matched) / len(findings)) if findings else None

    return ScoreResult(
        bug_matches=bug_matches,
        finding_matched=list(finding_matched),
        n_bugs=len(bugs),
        n_findings=len(findings),
        n_caught=n_caught,
        recall=recall,
        precision=precision,
        judge_calls=judge_calls,
        judge_usage=judge_usage,
    )


def cost_per_true_positive(total_input_tokens: int, total_output_tokens: int,
                           n_caught: int, *, price_in=5.0, price_out=25.0) -> Optional[float]:
    """USD per bug caught. Prices default to Opus 4.8 ($/MTok). None if 0 caught."""
    if n_caught == 0:
        return None
    cost = (total_input_tokens * price_in + total_output_tokens * price_out) / 1_000_000
    return cost / n_caught
